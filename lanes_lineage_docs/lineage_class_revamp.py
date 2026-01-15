"""
Augment running variant hex list using CDC Nowcast Tableau workbook.

Behavior:
- Treat RUNNING LIST as the source of truth.
- Append only "new" variants found in Tableau that are NOT already in running list.
- Do NOT overwrite running list colors (but write a QA file showing disagreements).

Write:
  - final_augmented_runninglist.csv
  - qa_new_variants_from_tableau.csv
  - qa_tableau_disagrees_with_runninglist.csv
  - tableau_best_guess.csv
  - tableau_conflicts_long.csv
"""

from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path

import polars as pl
import requests
from bs4 import BeautifulSoup

# -----------------------------
# Config
# -----------------------------

TABLEAU_URL = "https://public.tableau.com/workbooks/Variant_Proportions_Plus_Nowcasting_PREVIEW.twb"
RUNNINGLIST_CSV = "runninglist_lineage_hexcodes.csv"

OUT_FINAL = "final_augmented_runninglist.csv"
OUT_QA_NEW = "qa_new_variants_from_tableau.csv"
OUT_QA_MISMATCH = "qa_tableau_disagrees_with_runninglist.csv"
OUT_TABLEAU_BEST = "tableau_best_guess.csv"
OUT_TABLEAU_CONFLICTS = "tableau_conflicts_long.csv"

DROP_VALUES = {"", "Top", "VOC"}

# Tableau-derived additions should look like lineages; running list can include
# Ancestral, Unreportable, etc. (we do NOT filter those out of the running list)
LINEAGE_LIKE_PATTERN = (
    r"^(?:"
    r"X[A-Z0-9]{1,4}(?:\.\d+)*|"        # XFG.1, XEC.4, XBB.1.5, etc.
    r"[A-Z]{1,3}\.\d+(?:\.\d+)*|"       # KP.3.1.1, BA.2.86, JN.1, AY.4, etc.
    r"B\.\d+(?:\.\d+)*|"                # B.1.1.529 etc.
    r"[A-Z]+"                           # VBM, NA, etc.
    r")$"
)

HEADER_VARIANT_TOKENS = {"variant", "lineage", "lineage_name", "variant_name"}
HEADER_COLOR_TOKENS = {"hex", "hex_code", "hexcode", "color", "colour"}

# -----------------------------
# Helpers
# -----------------------------

def norm_variant(s: str | None) -> str:
    if s is None:
        return ""
    s = s.strip()
    s = s.strip('"').strip("'").strip()
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return s


def norm_hex(s: str | None) -> str:
    if s is None:
        return ""
    s = s.strip()
    if not s:
        return ""
    if not s.startswith("#"):
        s = "#" + s
    return s.upper()


def looks_like_hex(s: str) -> bool:
    return bool(re.fullmatch(r"#?[0-9A-Fa-f]{6}", (s or "").strip()))


def _cell_token(cell: str) -> str:
    """Normalize a header cell to a simple token for exact matching."""
    if cell is None:
        return ""
    c = str(cell).strip().lower()
    # collapse spaces/underscores for robustness
    c = re.sub(r"[\s\-]+", "_", c)
    return c


def find_header_row(csv_path: str) -> int:
    """
    Find the *true* header row.

    IMPORTANT: We only accept rows where a cell is EXACTLY 'variant' (or similar)
    and another cell is EXACTLY 'color'/'hex' (or similar). This avoids matching
    title rows like "Running Variant Hexcode List".
    """
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            toks = {_cell_token(c) for c in row}
            if (toks & HEADER_VARIANT_TOKENS) and (toks & HEADER_COLOR_TOKENS):
                return i
            if i > 80:
                break
    return 0


def load_running_list(csv_path: str) -> pl.DataFrame:
    header_row = find_header_row(csv_path)

    df = pl.read_csv(
        csv_path,
        skip_rows=header_row,
        has_header=True,
        ignore_errors=True,
        encoding="utf8",
    )

    # Normalize column names
    df = df.rename({c: _cell_token(c) for c in df.columns})

    # Identify columns
    variant_col = None
    hex_col = None
    for c in df.columns:
        if variant_col is None and c in HEADER_VARIANT_TOKENS:
            variant_col = c
        if hex_col is None and (c in HEADER_COLOR_TOKENS or "hex" in c or "color" in c):
            hex_col = c

    if not variant_col or not hex_col:
        raise ValueError(
            f"{csv_path} must have header columns like variant + color/hex_code. "
            f"Detected columns: {df.columns}"
        )

    out = (
        df.select(
            pl.col(variant_col).cast(pl.Utf8).alias("variant"),
            pl.col(hex_col).cast(pl.Utf8).alias("hex_code"),
        )
        .with_columns(
            pl.col("variant").map_elements(norm_variant, return_dtype=pl.Utf8),
            pl.col("hex_code").map_elements(norm_hex, return_dtype=pl.Utf8),
        )
        .filter(pl.col("variant").is_not_null() & (pl.col("variant") != ""))
        .filter(pl.col("hex_code").is_not_null() & (pl.col("hex_code") != ""))
        .unique(subset=["variant"], keep="first")
        .sort("variant")
    )

    return out


def extract_pairs_from_soup(soup: BeautifulSoup) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []

    for map_tag in soup.find_all("map"):
        map_to = norm_hex(map_tag.get("to", ""))

        # multibucket blocks
        for mb in map_tag.find_all("multibucket"):
            mb_to = norm_hex(mb.get("to", "")) or map_to
            if not looks_like_hex(mb_to):
                continue
            for b in mb.find_all("bucket"):
                val = norm_variant(b.get("value", "") or b.text)
                if val and val not in DROP_VALUES:
                    pairs.append((val, mb_to))

        # bucket blocks outside multibucket
        for b in map_tag.find_all("bucket", recursive=True):
            if b.find_parent("multibucket") is not None:
                continue
            b_to = norm_hex(b.get("to", "")) or map_to
            if not looks_like_hex(b_to):
                continue
            val = norm_variant(b.get("value", "") or b.text)
            if val and val not in DROP_VALUES:
                pairs.append((val, b_to))

    return pairs


def tableau_best_guess(url: str = TABLEAU_URL) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Returns:
      best: variant, tableau_hex
      conflicts_long: variant, tableau_hex, n  (only those with >1 unique hex)
    """
    print("Downloading Tableau workbook…")
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    twb_file = Path("nowcast_workbook.twb")
    twb_file.write_bytes(resp.content)

    with zipfile.ZipFile(twb_file, "r") as z:
        twb_names = [n for n in z.namelist() if n.endswith(".twb")]
        if not twb_names:
            raise RuntimeError("No .twb found inside downloaded workbook zip.")
        xml_bytes = z.read(twb_names[0])

    soup = BeautifulSoup(xml_bytes, "xml")
    pairs = extract_pairs_from_soup(soup)
    if not pairs:
        raise RuntimeError("No (variant,color) pairs extracted. Tableau XML structure may have changed.")

    df = pl.DataFrame(pairs, schema=["variant", "tableau_hex"], orient="row")

    df = (
        df.with_columns(
            pl.col("variant").map_elements(norm_variant, return_dtype=pl.Utf8),
            pl.col("tableau_hex").map_elements(norm_hex, return_dtype=pl.Utf8),
        )
        .filter(pl.col("variant").is_not_null() & (pl.col("variant") != ""))
        .filter(pl.col("tableau_hex").is_not_null() & (pl.col("tableau_hex") != ""))
        .filter(~pl.col("variant").is_in(list(DROP_VALUES)))
        # ONLY keep lineage-like strings from Tableau (running list can contain non-lineage labels)
        .filter(pl.col("variant").str.contains(LINEAGE_LIKE_PATTERN))
    )

    counts = (
        df.group_by(["variant", "tableau_hex"])
        .len()
        .rename({"len": "n"})
        .sort(["variant", "n"], descending=[False, True])
    )

    best = (
        counts.group_by("variant")
        .agg(pl.col("tableau_hex").first().alias("tableau_hex"))
        .sort("variant")
    )

    conflicts_long = (
        counts.join(
            counts.group_by("variant").agg(pl.col("tableau_hex").n_unique().alias("n_unique_hex")),
            on="variant",
            how="left",
        )
        .filter(pl.col("n_unique_hex") > 1)
        .select(["variant", "tableau_hex", "n"])
        .sort(["variant", "n"], descending=[False, True])
    )

    return best, conflicts_long


def main():
    # 0) Load running list FIRST (source of truth)
    running = load_running_list(RUNNINGLIST_CSV)
    print(f"Loaded running list: {running.height} variants")
    print("Running list sample:")
    print(running.head(10))

    # 1) Load tableau best guess (for discovering new CDC-tracked lineages + QA)
    tableau_best, tableau_conflicts = tableau_best_guess(TABLEAU_URL)

    # Save Tableau outputs for transparency
    tableau_best.write_csv(OUT_TABLEAU_BEST)
    tableau_conflicts.write_csv(OUT_TABLEAU_CONFLICTS)

    # 2) New variants = in Tableau but not in running list
    new_from_tableau = (
        tableau_best.join(running.select("variant"), on="variant", how="anti")
        .with_columns(pl.lit("tableau").alias("source"))
        .select(["variant", pl.col("tableau_hex").alias("hex_code"), "source"])
        .sort("variant")
    )
    new_from_tableau.write_csv(OUT_QA_NEW)

    # 3) Mismatches (do NOT overwrite running list; just report)
    mismatches = (
        running.join(tableau_best, on="variant", how="inner")
        .filter(pl.col("hex_code") != pl.col("tableau_hex"))
        .select(["variant", "hex_code", "tableau_hex"])
        .sort("variant")
    )
    mismatches.write_csv(OUT_QA_MISMATCH)

    # 4) Final augmented list = running list + appended new ones
    final = (
        running.with_columns(pl.lit("running_list").alias("source"))
        .select(["variant", "hex_code", "source"])
        .vstack(new_from_tableau.select(["variant", "hex_code", "source"]))
        .unique(subset=["variant"], keep="first")   # keeps running_list row if overlap exists
        .sort("variant")
    )
    final.write_csv(OUT_FINAL)

    print(f"Wrote {OUT_FINAL} ({final.height} total variants).")
    print(f"Wrote {OUT_QA_NEW} ({new_from_tableau.height} new variants from Tableau).")
    print(f"Wrote {OUT_QA_MISMATCH} ({mismatches.height} running-list variants where Tableau disagrees).")
    print(f"Wrote {OUT_TABLEAU_BEST} ({tableau_best.height} Tableau variants deduped).")
    print(f"Wrote {OUT_TABLEAU_CONFLICTS} ({tableau_conflicts.height} conflict rows).")

    # Sanity check: how many came from each source?
    print("Final source counts:")
    print(final.group_by("source").len().sort("len", descending=True))


if __name__ == "__main__":
    main()
