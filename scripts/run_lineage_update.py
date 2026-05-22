#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import subprocess
import sys
import pandas as pd

APPROVE_VALUES = {"y", "yes", "true", "approve", "approved"}

PENDING = Path("pull_hexcodes/pending_additions.csv")
QA_DISAGREEMENTS = Path("pull_hexcodes/qa_disagreements.csv")
RUNNING_LIST = Path("pull_hexcodes/final_augmented_runninglist.csv")

CLINICAL_OUT = Path("results/lineage_classifications.csv")
WW_OUT = Path("results/ww_lineage_classifications.csv")

REPORT = Path("lineage_update_run_report.md")


def log(lines, message):
    print(message)
    lines.append(message)


def run_cmd(lines, step_name, cmd):
    log(lines, f"\n## {step_name}")
    log(lines, f"Command: `{' '.join(cmd)}`")

    result = subprocess.run(cmd, text=True, capture_output=True)

    if result.stdout:
        log(lines, "\nSTDOUT:")
        log(lines, "```")
        log(lines, result.stdout.strip())
        log(lines, "```")

    if result.stderr:
        log(lines, "\nSTDERR:")
        log(lines, "```")
        log(lines, result.stderr.strip())
        log(lines, "```")

    if result.returncode != 0:
        log(lines, f"\n❌ FAILED: {step_name}")
        write_report(lines)
        sys.exit(result.returncode)

    log(lines, f"✅ Completed: {step_name}")


def write_report(lines):
    REPORT.write_text("\n".join(lines) + "\n")


def check_file_exists(lines, path):
    if not path.exists():
        log(lines, f"❌ Missing expected file: `{path}`")
        write_report(lines)
        sys.exit(1)
    log(lines, f"✅ Found expected file: `{path}`")


def check_pending_approvals(lines):
    log(lines, "\n## Manual approval check")

    check_file_exists(lines, PENDING)

    pending = pd.read_csv(PENDING)

    if pending.empty:
        log(lines, "✅ `pending_additions.csv` is empty. No approvals needed.")
        return

    approve_col = None
    for col in ["approve1", "approve"]:
        if col in pending.columns:
            approve_col = col
            break

    if approve_col is None:
        log(lines, "❌ Could not find approval column. Expected `approve1` or `approve`.")
        write_report(lines)
        sys.exit(1)

    approval_values = (
        pending[approve_col]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    unapproved = pending[~approval_values.isin(APPROVE_VALUES)]

    if len(unapproved) > 0:
        log(lines, f"🟡 STOP: {len(unapproved)} lineage(s) require manual approval.")
        log(lines, "")
        log(lines, "Manual action needed:")
        log(lines, f"1. Open `{PENDING}`")
        log(lines, f"2. Review new lineage rows")
        log(lines, f"3. Enter `yes` in `{approve_col}` for approved lineages")
        log(lines, "4. Re-run the GitHub Action manually")
        log(lines, "")
        log(lines, "Unapproved rows:")
        log(lines, "```")
        log(lines, unapproved.to_string(index=False))
        log(lines, "```")
        write_report(lines)
        sys.exit(2)

    log(lines, "✅ All pending lineage additions are approved.")


def check_qa_disagreements(lines):
    log(lines, "\n## QA disagreement check")

    check_file_exists(lines, QA_DISAGREEMENTS)

    qa = pd.read_csv(QA_DISAGREEMENTS)

    if len(qa) > 0:
        log(lines, f"🟡 STOP: `{QA_DISAGREEMENTS}` contains {len(qa)} row(s).")
        log(lines, "")
        log(lines, "Manual action needed:")
        log(lines, f"1. Open `{QA_DISAGREEMENTS}`")
        log(lines, "2. Resolve disagreements")
        log(lines, "3. Re-run the GitHub Action manually")
        log(lines, "")
        log(lines, "Rows requiring review:")
        log(lines, "```")
        log(lines, qa.to_string(index=False))
        log(lines, "```")
        write_report(lines)
        sys.exit(3)

    log(lines, "✅ No QA disagreements found.")


def validate_outputs(lines):
    log(lines, "\n## Output validation")

    required_common = {
        "lineage_extracted",
        "description",
        "status",
        "doh_variant_name",
        "who_name",
        "hex_code",
    }

    expected = {
        CLINICAL_OUT: required_common | {"doh_variant_name_tables"},
        WW_OUT: required_common | {"wastewater_variant_name"},
    }

    for path, required_cols in expected.items():
        check_file_exists(lines, path)

        df = pd.read_csv(path)
        missing = required_cols - set(df.columns)

        if missing:
            log(lines, f"❌ `{path}` is missing required columns: {sorted(missing)}")
            write_report(lines)
            sys.exit(4)

        if len(df) == 0:
            log(lines, f"❌ `{path}` has zero rows.")
            write_report(lines)
            sys.exit(5)

        log(lines, f"✅ `{path}` passed validation.")
        log(lines, f"   Rows: {len(df)}")
        log(lines, f"   Columns: {len(df.columns)}")


def main():
    lines = []
    lines.append("# Lineage Classification Update Run Report")
    lines.append(f"Run time: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")
    lines.append("This report records each automation step and flags where manual review is needed.")

    Path("results").mkdir(exist_ok=True)

    run_cmd(
        lines,
        "Step 1 — Pull latest CDC lineage updates",
        ["uv", "run", "pull_hexcodes/decision_tree.py"],
    )

    check_pending_approvals(lines)
    check_qa_disagreements(lines)

    run_cmd(
        lines,
        "Step 2 — Apply approved lineage updates",
        ["uv", "run", "pull_hexcodes/decision_tree.py"],
    )

    check_file_exists(lines, RUNNING_LIST)

    run_cmd(
        lines,
        "Step 3 — Generate clinical output",
        [
            "uv",
            "run",
            "main.py",
            "--workflow-type",
            "clinical",
            "--lineage-list",
            str(RUNNING_LIST),
            "-o",
            str(CLINICAL_OUT),
        ],
    )

    run_cmd(
        lines,
        "Step 4 — Generate wastewater output",
        [
            "uv",
            "run",
            "main.py",
            "--workflow-type",
            "wastewater",
            "--lineage-list",
            str(RUNNING_LIST),
            "-o",
            str(WW_OUT),
        ],
    )

    validate_outputs(lines)

    log(lines, "\n## Final status")
    log(lines, "✅ Pipeline completed successfully.")
    log(lines, "")
    log(lines, "Files updated:")
    log(lines, f"- `{RUNNING_LIST}`")
    log(lines, f"- `{PENDING}`")
    log(lines, f"- `{QA_DISAGREEMENTS}`")
    log(lines, f"- `{CLINICAL_OUT}`")
    log(lines, f"- `{WW_OUT}`")

    write_report(lines)


if __name__ == "__main__":
    main()