#!/usr/bin/env python3

from pathlib import Path
from datetime import datetime
import subprocess
import sys
import re
import pandas as pd

###############################################
# CONFIG
###############################################

APPROVE_VALUES = {"y", "yes", "true", "approve", "approved"}

HEX_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")

PENDING = Path("pull_hexcodes/pending_additions.csv")
QA_DISAGREEMENTS = Path("pull_hexcodes/qa_disagreements.csv")
RUNNING_LIST = Path("pull_hexcodes/final_augmented_runninglist.csv")

CLINICAL_OUT = Path("results/lineage_classifications.csv")
WW_OUT = Path("results/ww_lineage_classifications.csv")

REPORT = Path("lineage_update_run_report.md")

###############################################
# HELPERS
###############################################


def log(lines, message):
    print(message)
    lines.append(message)


def write_report(lines):
    REPORT.write_text("\n".join(lines) + "\n")


def fail_and_exit(lines, message, exit_code=1):
    log(lines, message)
    write_report(lines)
    sys.exit(exit_code)


def check_file_exists(lines, path):
    if not path.exists():
        fail_and_exit(
            lines,
            f"❌ FAILED: Missing expected file `{path}`",
            1
        )

    log(lines, f"✅ Found expected file: `{path}`")


###############################################
# COMMAND RUNNER
###############################################

def run_cmd(lines, step_name, cmd):

    log(lines, f"\n## {step_name}")
    log(lines, f"Command: `{' '.join(cmd)}`")

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True
    )

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
        fail_and_exit(
            lines,
            f"\n❌ FAILED: {step_name}",
            result.returncode
        )

    log(lines, f"✅ Completed: {step_name}")


###############################################
# VALIDATE PENDING ADDITIONS
###############################################

def validate_pending_additions(lines):

    log(lines, "\n## Pending additions validation")

    check_file_exists(lines, PENDING)

    pending = pd.read_csv(PENDING)

    ###########################################
    # REQUIRED COLUMNS
    ###########################################

    required_cols = {
        "variant",
        "tableau_hex",
        "approve",
    }

    missing = required_cols - set(pending.columns)

    if missing:
        fail_and_exit(
            lines,
            f"❌ FAILED: Missing required columns: {sorted(missing)}",
            10
        )

    ###########################################
    # NULL VARIANTS
    ###########################################

    null_variants = pending[pending["variant"].isna()]

    if len(null_variants) > 0:

        log(
            lines,
            "⚠️ WARNING: Rows with missing variant names detected."
        )

        log(lines, "Affected rows:")

        log(lines, "```")
        log(lines, null_variants.to_string(index=False))
        log(lines, "```")

    ###########################################
    # DUPLICATE VARIANTS
    ###########################################

    duplicates = pending[
        pending["variant"].duplicated(keep=False)
    ]

    if len(duplicates) > 0:

        log(
            lines,
            "⚠️ WARNING: Duplicate variants detected."
        )

        log(lines, "Affected rows:")

        log(lines, "```")
        log(lines, duplicates.to_string(index=False))
        log(lines, "```")

    ###########################################
    # INVALID HEX CODES
    ###########################################

    invalid_hex = pending[
        ~pending["tableau_hex"]
        .fillna("")
        .astype(str)
        .str.match(HEX_PATTERN)
    ]

    if len(invalid_hex) > 0:

        log(
            lines,
            "⚠️ WARNING: Invalid hex codes detected."
        )

        log(lines, "Affected rows:")

        log(lines, "```")
        log(lines, invalid_hex.to_string(index=False))
        log(lines, "```")

    log(lines, "✅ Pending additions validation complete.")


###############################################
# APPROVAL CHECK
###############################################

def check_pending_approvals(lines):

    log(lines, "\n## Manual approval check")

    check_file_exists(lines, PENDING)

    pending = pd.read_csv(PENDING)

    if pending.empty:
        log(
            lines,
            "✅ pending_additions.csv is empty. No approvals needed."
        )
        return

    ###########################################
    # DETECT APPROVAL COLUMN
    ###########################################

    approve_col = None

    for col in ["approve1", "approve"]:

        if col in pending.columns:
            approve_col = col
            break

    if approve_col is None:

        fail_and_exit(
            lines,
            "❌ FAILED: Could not find approval column.",
            2
        )

    ###########################################
    # FIND UNAPPROVED
    ###########################################

    approval_values = (
        pending[approve_col]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    unapproved = pending[
        ~approval_values.isin(APPROVE_VALUES)
    ]

    if len(unapproved) > 0:

        log(
            lines,
            f"🟡 STATUS: PAUSED FOR HUMAN REVIEW — "
            f"{len(unapproved)} lineage(s) require approval."
        )

        log(lines, "")

        log(lines, "NEXT ACTION REQUIRED:")

        log(lines, "1. Open pull_hexcodes/pending_additions.csv")

        log(
            lines,
            f"2. Review lineage rows"
        )

        log(
            lines,
            f"3. Enter yes in `{approve_col}` for approved rows"
        )

        log(lines, "4. Re-run the automation")

        log(lines, "")

        log(lines, "Unapproved rows:")

        log(lines, "```")
        log(lines, unapproved.to_string(index=False))
        log(lines, "```")

        write_report(lines)

        sys.exit(2)

    log(lines, "✅ All pending lineage additions are approved.")


###############################################
# QA DISAGREEMENT CHECK
###############################################

def check_qa_disagreements(lines):

    log(lines, "\n## QA disagreement check")

    check_file_exists(lines, QA_DISAGREEMENTS)

    qa = pd.read_csv(QA_DISAGREEMENTS)

    ###########################################
    # OPTIONAL MOCK TEST
    ###########################################
    # Uncomment temporarily to test failure path
    #
    # log(
    #     lines,
    #     "🟡 STATUS: PAUSED FOR HUMAN REVIEW — mock QA disagreement"
    # )
    #
    # write_report(lines)
    # sys.exit(3)

    ###########################################

    if len(qa) > 0:

        log(
            lines,
            f"🟡 STATUS: PAUSED FOR HUMAN REVIEW — "
            f"{len(qa)} QA disagreement row(s) detected."
        )

        log(lines, "")

        log(lines, "NEXT ACTION REQUIRED:")

        log(lines, "1. Open pull_hexcodes/qa_disagreements.csv")

        log(lines, "2. Review disagreement rows")

        log(lines, "3. Resolve lineage conflicts")

        log(lines, "4. Re-run the automation")

        log(lines, "")

        log(lines, "QA disagreement rows:")

        log(lines, "```")
        log(lines, qa.to_string(index=False))
        log(lines, "```")

        write_report(lines)

        sys.exit(3)

    log(lines, "✅ No QA disagreements found.")


###############################################
# OUTPUT VALIDATION
###############################################

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

            fail_and_exit(
                lines,
                f"❌ FAILED: `{path}` missing columns: {sorted(missing)}",
                4
            )

        if len(df) == 0:

            fail_and_exit(
                lines,
                f"❌ FAILED: `{path}` has zero rows.",
                5
            )

        log(lines, f"✅ `{path}` passed validation.")
        log(lines, f"Rows: {len(df)}")
        log(lines, f"Columns: {len(df.columns)}")


###############################################
# SUMMARY
###############################################

def summarize(lines):

    log(lines, "\n## SUMMARY")

    pending = pd.read_csv(PENDING)
    qa = pd.read_csv(QA_DISAGREEMENTS)

    log(lines, f"Pending lineage rows: {len(pending)}")

    approve_col = None

    for col in ["approve1", "approve"]:
        if col in pending.columns:
            approve_col = col
            break

    if approve_col:

        unapproved_count = len(
            pending[
                ~pending[approve_col]
                .fillna("")
                .astype(str)
                .str.lower()
                .isin(APPROVE_VALUES)
            ]
        )

        log(
            lines,
            f"Pending approvals remaining: {unapproved_count}"
        )

    log(lines, f"QA disagreements: {len(qa)}")

    if CLINICAL_OUT.exists():
        clinical = pd.read_csv(CLINICAL_OUT)

        log(
            lines,
            f"Clinical output rows: {len(clinical)}"
        )

    if WW_OUT.exists():
        ww = pd.read_csv(WW_OUT)

        log(
            lines,
            f"Wastewater output rows: {len(ww)}"
        )


###############################################
# MAIN
###############################################

def main():

    lines = []

    lines.append("# Lineage Classification Update Run Report")

    lines.append(
        f"Run time: "
        f"{datetime.now().isoformat(timespec='seconds')}"
    )

    lines.append("")

    lines.append(
        "This report records automation steps, "
        "warnings, validation checks, and required "
        "manual review actions."
    )

    Path("results").mkdir(exist_ok=True)

    ###########################################
    # STEP 1
    ###########################################

    run_cmd(
        lines,
        "Step 1 — Pull latest CDC lineage updates",
        ["uv", "run", "pull_hexcodes/decision_tree.py"],
    )

    ###########################################
    # VALIDATE PENDING
    ###########################################

    validate_pending_additions(lines)

    ###########################################
    # APPROVAL CHECK
    ###########################################

    check_pending_approvals(lines)

    ###########################################
    # QA CHECK
    ###########################################

    check_qa_disagreements(lines)

    ###########################################
    # STEP 2
    ###########################################

    run_cmd(
        lines,
        "Step 2 — Apply approved lineage updates",
        ["uv", "run", "pull_hexcodes/decision_tree.py"],
    )

    check_file_exists(lines, RUNNING_LIST)

    ###########################################
    # STEP 3
    ###########################################

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

    ###########################################
    # STEP 4
    ###########################################

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

    ###########################################
    # VALIDATE OUTPUTS
    ###########################################

    validate_outputs(lines)

    ###########################################
    # SUMMARY
    ###########################################

    summarize(lines)

    ###########################################
    # FINAL STATUS
    ###########################################

    log(lines, "\n## FINAL STATUS")

    log(lines, "✅ SUCCESS: Pipeline completed successfully.")

    log(lines, "")

    log(lines, "Updated files:")

    log(lines, f"- `{RUNNING_LIST}`")
    log(lines, f"- `{PENDING}`")
    log(lines, f"- `{QA_DISAGREEMENTS}`")
    log(lines, f"- `{CLINICAL_OUT}`")
    log(lines, f"- `{WW_OUT}`")

    write_report(lines)


if __name__ == "__main__":
    main()