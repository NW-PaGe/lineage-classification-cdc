"""
Augment running variant hex list using CDC Nowcast Tableau workbook.

Decision-tree/approval workflow:
- RUNNING LIST is source of truth (never overwritten).
- Tableau is used ONLY to propose *new* variants (CDC-tracked / disaggregated lineages).
- New variants go into pending_additions.csv for human approval.
- Only rows with approve=yes (or y/true/approved) get added to the final file.

Outputs:
  - final_augmented_runninglist.csv
  - pending_additions.csv
  - qa_disagreements.csv (optional; Tableau vs running-list differences for existing variants)
  - retired/final_augmented_runninglist_YYYY-MM-DD.csv (automatic archive before overwrite)
"""

from __future__ import annotations

import csv
import re
import shutil
import zipfile
from datetime import date, datetime
from pathlib import Path

import polars as pl
import requests
from bs4 import BeautifulSoup

# -----------------------------
# Config
# -----------------------------
TABLEAU_URL = "https://public.tableau.com/workbooks/Variant_Proportions_Plus_Nowcasting_PREVIEW.twb"
BASE_DIR = Path(".")  # current repo directory
RUNNINGLIST_CSV = BASE_DIR / "runninglist_lineage_hexcodes.csv"
OUT_FINAL = BASE_DIR / "final_augmented_runninglist.csv"
OUT_PENDING = BASE_DIR / "pending_additions.csv"
OUT_QA_DISAGREE = BASE_DIR / "qa_disagreements.csv"
RETIRED_DIR = BASE_DIR / "retired"
WRITE_QA_DISAGREEMENTS = True
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

# We intentionally use exact header tokens so title rows like
# "Running Variant Hexcode List" won't be mistaken for headers.
HEADER_VARIANT_TOKENS = {"variant", "lineage", "lineage_name", "variant_name"}
HEADER_COLOR_TOKENS = {"hex", "hex_code", "hexcode", "color", "colour"}

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

APPROVE_VALUES = {"y", "yes", "true", "approve", "approved"}


# -----------------------------
# Helpers
# -----------------------------
def norm_variant(s: str | None) -> str:
    if s is None:
        return ""
    s = str(s).strip().strip('"').strip("'").strip()
    s = s.replace("\u2013", "-").replace("\u2014", "-")
    return s


def norm_hex(s: str | None) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    if not s:
        return ""
    if not s.startswith("#"):
        s = "#" + s
    return s.upper()


def looks_like_hex(s: str) -> bool:
    return bool(HEX_RE.fullmatch((s or "").strip()))


def _cell_token(cell: str) -> str:
    """Normalize a header cell to a stable token for exact matching."""
    if cell is None:
        return ""
    c = str(cell).strip().lower()
    c = re.sub(r"[\s\-]+", "_", c)
    return c


def find_header_row(csv_path: str) -> int:
    """
    Detect the *true* header row (avoids title rows like 'Running Variant Hexcode List').
    We only accept rows where a cell token is EXACTLY one of the variant tokens and
    another cell token is EXACTLY one of the color tokens.
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

    variant_col = None
    hex_col = None
    for c in df.columns:
        if variant_col is None and c in HEADER_VARIANT_TOKENS:
            variant_col = c
        if hex_col is None and (c in HEADER_COLOR_TOKENS or "hex" in c or "color" in c):
            hex_col = c

    if not variant_col or not hex_col or variant_col == hex_col:
        raise ValueError(
            f"{csv_path} must have separate columns for variant + hex/color.\n"
            f"Detected variant_col={variant_col}, hex_col={hex_col}, columns={df.columns}"
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
        .unique(subset=["variant"], keep="first")  # running list should be unique by variant
        .sort("variant")
    )

    return out


def extract_pairs_from_soup(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """
    Return list of (variant, hex) pairs from Tableau TWB XML.

    Handles common patterns:
      - map->multibucket->bucket
      - map->bucket (with value= or text content)
    """
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


def tableau_best_guess(url: str) -> tuple[pl.DataFrame, pl.DataFrame]:
    """
    Returns:
      best:      variant, tableau_hex         (mode color per variant)
      conflicts: variant, tableau_hex, n      (only variants with >1 unique hex in workbook)
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
        raise RuntimeError("No (variant,color) pairs extracted; Tableau XML may have changed.")

    df = pl.DataFrame(pairs, schema=["variant", "tableau_hex"], orient="row")

    df = (
        df.with_columns(
            pl.col("variant").map_elements(norm_variant, return_dtype=pl.Utf8),
            pl.col("tableau_hex").map_elements(norm_hex, return_dtype=pl.Utf8),
        )
        .filter(pl.col("variant").is_not_null() & (pl.col("variant") != ""))
        .filter(pl.col("tableau_hex").is_not_null() & (pl.col("tableau_hex") != ""))
        .filter(~pl.col("variant").is_in(list(DROP_VALUES)))
        # ONLY keep lineage-like strings from Tableau (running list may include non-lineage labels)
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

    conflicts = (
        counts.join(
            counts.group_by("variant").agg(pl.col("tableau_hex").n_unique().alias("n_unique_hex")),
            on="variant",
            how="left",
        )
        .filter(pl.col("n_unique_hex") > 1)
        .select(["variant", "tableau_hex", "n"])
        .sort(["variant", "n"], descending=[False, True])
    )

    return best, conflicts


def load_pending(path: str) -> pl.DataFrame:
    """
    pending_additions.csv schema:
      variant, tableau_hex, final_hex, approve, note, has_conflict
    """
    p = Path(path)
    if not p.exists():
        return pl.DataFrame(
            schema={
                "variant": pl.Utf8,
                "tableau_hex": pl.Utf8,
                "final_hex": pl.Utf8,
                "approve": pl.Utf8,
                "note": pl.Utf8,
                "has_conflict": pl.Int64,
            }
        )

    df = pl.read_csv(path, ignore_errors=True, encoding="utf8")
    df = df.rename({c: _cell_token(c) for c in df.columns})

    # Ensure expected columns exist
    needed = ["variant", "tableau_hex", "final_hex", "approve", "note", "has_conflict"]
    for col in needed:
        if col not in df.columns:
            default = 0 if col == "has_conflict" else ""
            df = df.with_columns(pl.lit(default).alias(col))

    return (
        df.select(needed)
        .with_columns(
            pl.col("variant").cast(pl.Utf8).map_elements(norm_variant, return_dtype=pl.Utf8),
            pl.col("tableau_hex").cast(pl.Utf8).map_elements(norm_hex, return_dtype=pl.Utf8),
            pl.col("final_hex").cast(pl.Utf8).map_elements(norm_hex, return_dtype=pl.Utf8),
            pl.col("approve").cast(pl.Utf8).fill_null("").str.to_lowercase(),
            pl.col("note").cast(pl.Utf8).fill_null(""),
            pl.col("has_conflict").cast(pl.Int64).fill_null(0),
        )
        .filter(pl.col("variant") != "")
        .unique(subset=["variant"], keep="first")
        .sort("variant")
    )


def archive_previous_final(out_final: str, retired_dir: str = RETIRED_DIR) -> None:
    """
    If out_final exists, move it into retired_dir with today's date.
    Avoid overwriting if multiple runs happen the same day.
    """
    final_path = Path(out_final)
    if not final_path.exists():
        return

    retired_path = Path(retired_dir)
    retired_path.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    base = retired_path / f"{final_path.stem}_{today}{final_path.suffix}"

    candidate = base
    i = 1
    while candidate.exists():
        candidate = retired_path / f"{final_path.stem}_{today}_{i}{final_path.suffix}"
        i += 1

    shutil.move(str(final_path), str(candidate))
    print(f"Archived previous {final_path.name} -> {candidate}")


def main():
    # 0) Load running list FIRST (source of truth)
    running = load_running_list(RUNNINGLIST_CSV)

    # 1) Load Tableau best guess (for proposing new variants + QA)
    tableau_best, tableau_conflicts = tableau_best_guess(TABLEAU_URL)

    # 2) Candidates = Tableau variants not in running list
    candidates = (
        tableau_best.join(running.select("variant"), on="variant", how="anti")
        .with_columns(
            pl.lit("").alias("final_hex"),
            pl.lit("").alias("approve"),
            pl.lit("").alias("note"),
        )
        .join(
            tableau_conflicts.group_by("variant").len().rename({"len": "has_conflict"}),
            on="variant",
            how="left",
        )
        .with_columns(pl.col("has_conflict").fill_null(0))
        .select(["variant", "tableau_hex", "final_hex", "approve", "note", "has_conflict"])
        .sort("variant")
    )

    # 3) Merge with existing pending to preserve approvals/overrides (final_hex/approve/note)
    pending_old = load_pending(OUT_PENDING)

    pending = (
        candidates.join(
            pending_old.select(["variant", "final_hex", "approve", "note"]),
            on="variant",
            how="left",
        )
        .with_columns(
            pl.coalesce([pl.col("final_hex_right"), pl.col("final_hex")]).alias("final_hex"),
            pl.coalesce([pl.col("approve_right"), pl.col("approve")]).alias("approve"),
            pl.coalesce([pl.col("note_right"), pl.col("note")]).alias("note"),
        )
        .drop(["final_hex_right", "approve_right", "note_right"])
        .unique(subset=["variant"], keep="first")
        .sort("variant")
    )
    pending.write_csv(OUT_PENDING)

    # 4) Approved additions only (final_hex overrides tableau_hex if provided)
    approved = (
        pending
        .with_columns(pl.col("approve").fill_null("").str.to_lowercase())
        .filter(pl.col("approve").is_in(list(APPROVE_VALUES)))
        .with_columns(
            pl.when(pl.col("final_hex") != "")
            .then(pl.col("final_hex"))
            .otherwise(pl.col("tableau_hex"))
            .alias("hex_code")
        )
        .select(["variant", "hex_code"])
        .with_columns(pl.lit("tableau_approved").alias("source"))
        .sort("variant")
    )

    # 5) Optional QA: Tableau disagrees with running list (FYI; does not overwrite)
    if WRITE_QA_DISAGREEMENTS:
        disagreements = (
            running.join(tableau_best, on="variant", how="inner")
            .filter(pl.col("hex_code") != pl.col("tableau_hex"))
            .select(["variant", "hex_code", "tableau_hex"])
            .sort("variant")
        )
        disagreements.write_csv(OUT_QA_DISAGREE)

    # 6) Final = running list + approved additions (running list wins on overlap)
    final = (
        running.with_columns(pl.lit("running_list").alias("source"))
        .select(["variant", "hex_code", "source"])
        .vstack(approved.select(["variant", "hex_code", "source"]))
        .unique(subset=["variant"], keep="first")
        .sort("variant")
    )

    # Archive previous final before overwriting
    archive_previous_final(OUT_FINAL, retired_dir=RETIRED_DIR)

    # Write new final
    final.write_csv(OUT_FINAL)

    # Console summary
    pending_unapproved = (
        pending
        .with_columns(pl.col("approve").fill_null("").str.to_lowercase())
        .filter(~pl.col("approve").is_in(list(APPROVE_VALUES)))
        .height
    )

    print(f"Loaded running list: {running.height} variants")
    print(f"Found new Tableau candidates: {candidates.height}")
    print(f"Wrote {OUT_PENDING} ({pending.height} rows; {pending_unapproved} awaiting approval)")
    print(f"Approved additions included: {approved.height}")
    print(f"Wrote {OUT_FINAL} ({final.height} total variants)")
    if WRITE_QA_DISAGREEMENTS:
        print(f"Wrote {OUT_QA_DISAGREE} (FYI only; does not overwrite running list)")
    print(f"Run complete: {datetime.now().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
