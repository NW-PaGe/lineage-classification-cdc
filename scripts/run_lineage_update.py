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

APPROVE_VALUES = {
    "y",
    "yes",
    "true",
    "approve",
    "approved",
}

REJECT_VALUES = {
    "n",
    "no",
    "reject",
    "rejected",
}

PENDING_VALUES = {
    "",
    "pending",
    "review",
    "needs_review",
}

HEX_PATTERN = re.compile(
    r"^#[0-9A-Fa-f]{6}$"
)

PENDING = Path(
    "pull_hexcodes/pending_additions.csv"
)

QA_DISAGREEMENTS = Path(
    "pull_hexcodes/qa_disagreements.csv"
)

RUNNING_LIST = Path(
    "pull_hexcodes/final_augmented_runninglist.csv"
)

CLINICAL_OUT = Path(
    "results/lineage_classifications.csv"
)

WW_OUT = Path(
    "results/ww_lineage_classifications.csv"
)

REPORT = Path(
    "lineage_update_run_report.md"
)

###############################################
# HELPERS
###############################################


def log(lines, message):

    print(message)

    lines.append(message)


def write_report(lines):

    REPORT.write_text(
        "\n".join(lines) + "\n"
    )


def pause_for_review(
    lines,
    message,
    exit_code=1,
):

    log(lines, "")

    log(
        lines,
        f"🟡 STATUS: PAUSED FOR HUMAN REVIEW — {message}"
    )

    log(lines, "")

    log(lines, "## FINAL STATUS")

    log(
        lines,
        "🟡 PAUSED FOR HUMAN REVIEW"
    )

    write_report(lines)

    sys.exit(exit_code)


def fail_and_exit(
    lines,
    message,
    exit_code=1,
):

    log(lines, "")

    log(
        lines,
        f"❌ FAILED: {message}"
    )

    log(lines, "")

    log(lines, "## FINAL STATUS")

    log(
        lines,
        "❌ PIPELINE FAILED"
    )

    write_report(lines)

    sys.exit(exit_code)


def check_file_exists(
    lines,
    path,
):

    if not path.exists():

        fail_and_exit(
            lines,
            f"Missing expected file `{path}`",
            1,
        )

    log(
        lines,
        f"✅ Found expected file: `{path}`"
    )


###############################################
# COMMAND RUNNER
###############################################

def run_cmd(
    lines,
    step_name,
    cmd,
):

    log(lines, f"\n## {step_name}")

    log(
        lines,
        f"Command: `{' '.join(cmd)}`"
    )

    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
    )

    if result.stdout:

        log(lines, "\nSTDOUT:")

        log(lines, "```")

        log(
            lines,
            result.stdout.strip(),
        )

        log(lines, "```")

    if result.stderr:

        log(lines, "\nSTDERR:")

        log(lines, "```")

        log(
            lines,
            result.stderr.strip(),
        )

        log(lines, "```")

    if result.returncode != 0:

        fail_and_exit(
            lines,
            step_name,
            result.returncode,
        )

    log(
        lines,
        f"✅ Completed: {step_name}"
    )


###############################################
# VALIDATE PENDING ADDITIONS
###############################################

def validate_pending_additions(
    lines,
):

    log(
        lines,
        "\n## Pending additions validation"
    )

    check_file_exists(
        lines,
        PENDING,
    )

    pending = pd.read_csv(
        PENDING,
        keep_default_na=False,
    )

    ###########################################
    # REQUIRED COLUMNS
    ###########################################

    required_cols = {
        "variant",
        "tableau_hex",
        "approve",
    }

    missing = (
        required_cols
        - set(pending.columns)
    )

    if missing:

        fail_and_exit(
            lines,
            f"Missing required columns: {sorted(missing)}",
            10,
        )

    ###########################################
    # NORMALIZE VARIANT COLUMN
    ###########################################

    pending["variant"] = (
        pending["variant"]
        .astype(str)
        .str.strip()
    )

    ###########################################
    # NULL / BLANK VARIANTS
    ###########################################

    null_variants = pending[
        (
            pending["variant"] == ""
        )
        |
        (
            pending["variant"]
            .str.lower()
            .isin(
                [
                    "nan",
                    "none",
                    "null",
                ]
            )
        )
    ]

    if len(null_variants) > 0:

        log(lines, "")

        log(
            lines,
            "⚠️ Rows with missing variant names detected."
        )

        log(lines, "")

        log(lines, "Affected rows:")

        log(lines, "```")

        log(
            lines,
            null_variants.to_string(
                index=False
            ),
        )

        log(lines, "```")

        log(lines, "")

        log(
            lines,
            "NEXT ACTION REQUIRED:"
        )

        log(
            lines,
            "1. Review pending_additions.csv"
        )

        log(
            lines,
            "2. Determine why variant values are missing"
        )

        log(
            lines,
            "3. Correct upstream lineage assignment issue"
        )

        log(
            lines,
            "4. Re-run automation"
        )

        pause_for_review(
            lines,
            "Rows with missing variant names detected.",
            11,
        )

    ###########################################
    # DUPLICATE VARIANTS
    ###########################################

    duplicates = pending[
        pending["variant"]
        .duplicated(keep=False)
    ]

    if len(duplicates) > 0:

        log(lines, "")

        log(
            lines,
            "⚠️ Duplicate variants detected."
        )

        log(lines, "")

        log(lines, "Affected rows:")

        log(lines, "```")

        log(
            lines,
            duplicates.to_string(
                index=False
            ),
        )

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

        log(lines, "")

        log(
            lines,
            "⚠️ Invalid hex codes detected."
        )

        log(lines, "")

        log(lines, "Affected rows:")

        log(lines, "```")

        log(
            lines,
            invalid_hex.to_string(
                index=False
            ),
        )

        log(lines, "```")

        pause_for_review(
            lines,
            "Invalid hex codes detected.",
            12,
        )

    ###########################################
    # VALIDATION SUMMARY
    ###########################################

    log(lines, "")

    log(lines, "Validation summary:")

    log(
        lines,
        f"- Missing variant rows: {len(null_variants)}"
    )

    log(
        lines,
        f"- Duplicate variants: {len(duplicates)}"
    )

    log(
        lines,
        f"- Invalid hex codes: {len(invalid_hex)}"
    )

    log(lines, "")

    log(
        lines,
        "✅ Pending additions validation complete."
    )


###############################################
# APPROVAL CHECK
###############################################

def check_pending_approvals(
    lines,
):

    log(
        lines,
        "\n## Manual approval check"
    )

    check_file_exists(
        lines,
        PENDING,
    )

    pending = pd.read_csv(
        PENDING,
        keep_default_na=False,
    )

    if pending.empty:

        log(
            lines,
            "✅ pending_additions.csv is empty. No approvals needed."
        )

        return

    approve_col = None

    for col in [
        "approve1",
        "approve",
    ]:

        if col in pending.columns:

            approve_col = col

            break

    if approve_col is None:

        fail_and_exit(
            lines,
            "Could not find approval column.",
            2,
        )

    approval_values = (
        pending[approve_col]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    ###########################################
    # ONLY PENDING ROWS BLOCK WORKFLOW
    ###########################################

    unapproved = pending[
        approval_values.isin(
            PENDING_VALUES
        )
    ]

    if len(unapproved) > 0:

        log(lines, "")

        log(
            lines,
            f"🟡 STATUS: PAUSED FOR HUMAN REVIEW — "
            f"{len(unapproved)} lineage(s) still pending review."
        )

        log(lines, "")

        log(
            lines,
            "NEXT ACTION REQUIRED:"
        )

        log(
            lines,
            "1. Open pull_hexcodes/pending_additions.csv"
        )

        log(
            lines,
            "2. Review lineage rows"
        )

        log(
            lines,
            "3. Enter:"
        )

        log(
            lines,
            "   - yes = approve"
        )

        log(
            lines,
            "   - no = intentionally reject"
        )

        log(
            lines,
            "   - pending = unresolved"
        )

        log(
            lines,
            "4. Re-run the automation"
        )

        log(lines, "")

        log(
            lines,
            "Showing first 10 pending rows:"
        )

        log(lines, "```")

        log(
            lines,
            unapproved.head(10)
            .to_string(index=False),
        )

        log(lines, "```")

        log(lines, "")

        log(
            lines,
            "See lineage_update_run_report.md for full details."
        )

        pause_for_review(
            lines,
            "Pending lineage reviews remain.",
            2,
        )

    ###########################################
    # SUMMARY
    ###########################################

    approved_count = len(
        pending[
            approval_values.isin(
                APPROVE_VALUES
            )
        ]
    )

    rejected_count = len(
        pending[
            approval_values.isin(
                REJECT_VALUES
            )
        ]
    )

    log(lines, "")

    log(
        lines,
        "Approval summary:"
    )

    log(
        lines,
        f"- Approved rows: {approved_count}"
    )

    log(
        lines,
        f"- Rejected rows: {rejected_count}"
    )

    log(
        lines,
        "✅ No pending lineage reviews remain."
    )


###############################################
# QA DISAGREEMENT CHECK
###############################################

def check_qa_disagreements(
    lines,
):

    log(
        lines,
        "\n## QA disagreement check"
    )

    check_file_exists(
        lines,
        QA_DISAGREEMENTS,
    )

    qa = pd.read_csv(
        QA_DISAGREEMENTS,
        keep_default_na=False,
    )

    if len(qa) > 0:

        log(lines, "")

        log(
            lines,
            f"🟡 STATUS: PAUSED FOR HUMAN REVIEW — "
            f"{len(qa)} QA disagreement row(s) detected."
        )

        log(lines, "")

        log(
            lines,
            "NEXT ACTION REQUIRED:"
        )

        log(
            lines,
            "1. Open pull_hexcodes/qa_disagreements.csv"
        )

        log(
            lines,
            "2. Review disagreement rows"
        )

        log(
            lines,
            "3. Resolve lineage conflicts"
        )

        log(
            lines,
            "4. Re-run the automation"
        )

        log(lines, "")

        log(
            lines,
            "Showing first 10 QA disagreement rows:"
        )

        log(lines, "```")

        log(
            lines,
            qa.head(10)
            .to_string(index=False),
        )

        log(lines, "```")

        log(lines, "")

        log(
            lines,
            "See lineage_update_run_report.md for full details."
        )

        log(lines, "")

        log(
            lines,
            "⚠️ QA disagreements detected but workflow will continue."
        )

        log(
            lines,
            "Running list remains the source of truth."
        )

        log(
            lines,
            "Review qa_disagreements.csv separately if CDC Nowcast has been updated and hex code is available for comparison."
        )


###############################################
# OUTPUT VALIDATION
###############################################

def validate_outputs(
    lines,
):

    log(
        lines,
        "\n## Output validation"
    )

    required_common = {
        "lineage_extracted",
        "Description",
        "status",
        "who_name",
        "hex_code",
    }

    expected = {
        CLINICAL_OUT:
            required_common
            | {"doh_variant_name_tables"},

        WW_OUT:
            required_common
            | {"wastewater_variant_name"},
    }

    for path, required_cols in expected.items():

        check_file_exists(
            lines,
            path,
        )

        df = pd.read_csv(
            path,
            keep_default_na=False,
        )

        missing = (
            required_cols
            - set(df.columns)
        )

        if missing:

            fail_and_exit(
                lines,
                f"`{path}` missing columns: {sorted(missing)}",
                4,
            )

        if len(df) == 0:

            fail_and_exit(
                lines,
                f"`{path}` has zero rows.",
                5,
            )

        log(
            lines,
            f"✅ `{path}` passed validation."
        )

        log(
            lines,
            f"Rows: {len(df)}"
        )

        log(
            lines,
            f"Columns: {len(df.columns)}"
        )


###############################################
# SUMMARY
###############################################

def summarize(
    lines,
):

    log(lines, "\n## SUMMARY")

    pending = pd.read_csv(
        PENDING,
        keep_default_na=False,
    )

    qa = pd.read_csv(
        QA_DISAGREEMENTS,
        keep_default_na=False,
    )

    approval_values = (
        pending["approve"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    log(
        lines,
        f"Pending lineage rows: {len(pending)}"
    )

    log(
        lines,
        f"Approved rows: "
        f"{len(pending[approval_values.isin(APPROVE_VALUES)])}"
    )

    log(
        lines,
        f"Rejected rows: "
        f"{len(pending[approval_values.isin(REJECT_VALUES)])}"
    )

    log(
        lines,
        f"Still pending review: "
        f"{len(pending[approval_values.isin(PENDING_VALUES)])}"
    )

    log(
        lines,
        f"QA disagreements: {len(qa)}"
    )

    if CLINICAL_OUT.exists():

        clinical = pd.read_csv(
            CLINICAL_OUT,
            keep_default_na=False,
        )

        log(
            lines,
            f"Clinical output rows: {len(clinical)}"
        )

    if WW_OUT.exists():

        ww = pd.read_csv(
            WW_OUT,
            keep_default_na=False,
        )

        log(
            lines,
            f"Wastewater output rows: {len(ww)}"
        )


###############################################
# MAIN
###############################################

def main():

    lines = []

    lines.append(
        "# Lineage Classification Update Run Report"
    )

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

    Path("results").mkdir(
        exist_ok=True
    )

    ###########################################
    # STEP 1
    ###########################################

    run_cmd(
        lines,
        "Step 1 — Pull latest CDC lineage updates",
        [
            "uv",
            "run",
            "pull_hexcodes/decision_tree.py",
        ],
    )

    ###########################################
    # VALIDATE PENDING
    ###########################################

    validate_pending_additions(
        lines
    )

    ###########################################
    # APPROVAL CHECK
    ###########################################

    check_pending_approvals(
        lines
    )

    ###########################################
    # QA CHECK
    ###########################################

    check_qa_disagreements(
        lines
    )

    ###########################################
    # STEP 2
    ###########################################

    run_cmd(
        lines,
        "Step 2 — Apply approved lineage updates",
        [
            "uv",
            "run",
            "pull_hexcodes/decision_tree.py",
        ],
    )

    check_file_exists(
        lines,
        RUNNING_LIST,
    )

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

    validate_outputs(
        lines
    )

    ###########################################
    # SUMMARY
    ###########################################

    summarize(lines)

    ###########################################
    # FINAL STATUS
    ###########################################

    log(lines, "\n## FINAL STATUS")

    log(
        lines,
        "✅ SUCCESS: Pipeline completed successfully."
    )

    log(lines, "")

    log(lines, "Updated files:")

    log(
        lines,
        f"- `{RUNNING_LIST}`"
    )

    log(
        lines,
        f"- `{PENDING}`"
    )

    log(
        lines,
        f"- `{QA_DISAGREEMENTS}`"
    )

    log(
        lines,
        f"- `{CLINICAL_OUT}`"
    )

    log(
        lines,
        f"- `{WW_OUT}`"
    )

    write_report(lines)


if __name__ == "__main__":
    main()