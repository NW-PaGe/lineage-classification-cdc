# Lineage Classification Update Run Report
Run time: 2026-08-20T17:41:44

This report records automation steps, warnings, validation checks, and required manual review actions.

## Step 1 — Pull latest CDC lineage updates
Command: `uv run pull_hexcodes/decision_tree.py`

STDOUT:
```
Downloading Tableau workbook…
Archived previous pending_additions.csv -> /home/dah0303/lineage-classification-cdc/pull_hexcodes/retired/pending_additions_2026-08-20_2.csv
Archived previous final_augmented_runninglist.csv -> /home/dah0303/lineage-classification-cdc/pull_hexcodes/retired/final_augmented_runninglist_2026-08-20_2.csv
Loaded running list: 121 variants
Found new Tableau candidates: 44
Wrote /home/dah0303/lineage-classification-cdc/pull_hexcodes/pending_additions.csv (44 rows; 25 awaiting approval)
Approved additions included: 19
Wrote /home/dah0303/lineage-classification-cdc/pull_hexcodes/final_augmented_runninglist.csv (140 total variants)
Wrote /home/dah0303/lineage-classification-cdc/pull_hexcodes/qa_disagreements.csv (FYI only; does not overwrite running list)
Run complete: 2026-08-20T17:41:47
```
✅ Completed: Step 1 — Pull latest CDC lineage updates

## Pending additions validation
✅ Found expected file: `pull_hexcodes/pending_additions.csv`

Validation summary:
- Missing variant rows: 0
- Duplicate variants: 0
- Invalid hex codes: 0

✅ Pending additions validation complete.

## Manual approval check
✅ Found expected file: `pull_hexcodes/pending_additions.csv`

Approval summary:
- Approved rows: 19
- Rejected rows: 25
✅ No pending lineage reviews remain.

## QA disagreement check
✅ Found expected file: `pull_hexcodes/qa_disagreements.csv`

🟡 STATUS: PAUSED FOR HUMAN REVIEW — 21 QA disagreement row(s) detected.

NEXT ACTION REQUIRED:
1. Open pull_hexcodes/qa_disagreements.csv
2. Review disagreement rows
3. Resolve lineage conflicts
4. Re-run the automation

Showing first 10 QA disagreement rows:
```
  variant hex_code tableau_hex
B.1.1.529  #FFBE7D     #E26028
B.1.617.2  #B39DDB     #F28E2B
     BA.2  #9CCD67     #E15759
BA.2.12.1  #7CB342     #EDC948
  BA.2.86  #D770EE     #D771F1
     BA.5  #80CBC4     #76B7B2
     BF.7  #81D4FA     #A0CBE8
     JN.1  #61018F     #660099
  JN.1.18  #4AF32F     #4DF230
JN.1.18.6  #D16F2C     #E16B1D
```

See lineage_update_run_report.md for full details.

⚠️ QA disagreements detected but workflow will continue.
Running list remains the source of truth.
Review qa_disagreements.csv separately if CDC Nowcast has been updated and hex code is available for comparison.

## Step 2 — Apply approved lineage updates
Command: `uv run pull_hexcodes/decision_tree.py`

STDOUT:
```
Downloading Tableau workbook…
Archived previous pending_additions.csv -> /home/dah0303/lineage-classification-cdc/pull_hexcodes/retired/pending_additions_2026-08-20_3.csv
Archived previous final_augmented_runninglist.csv -> /home/dah0303/lineage-classification-cdc/pull_hexcodes/retired/final_augmented_runninglist_2026-08-20_3.csv
Loaded running list: 121 variants
Found new Tableau candidates: 44
Wrote /home/dah0303/lineage-classification-cdc/pull_hexcodes/pending_additions.csv (44 rows; 25 awaiting approval)
Approved additions included: 19
Wrote /home/dah0303/lineage-classification-cdc/pull_hexcodes/final_augmented_runninglist.csv (140 total variants)
Wrote /home/dah0303/lineage-classification-cdc/pull_hexcodes/qa_disagreements.csv (FYI only; does not overwrite running list)
Run complete: 2026-08-20T17:41:49
```
✅ Completed: Step 2 — Apply approved lineage updates
✅ Found expected file: `pull_hexcodes/final_augmented_runninglist.csv`
Running list size check passed (140 rows).

## Step 3 — Generate clinical output
Command: `uv run main.py --workflow-type clinical --lineage-list pull_hexcodes/final_augmented_runninglist.csv -o results/lineage_classifications.csv`

STDOUT:
```
Hello from lineage-classification-cdc! 

lineage notes were pulled successfully. 

Lineage list with hexcodes sourced from pull_hexcodes/final_augmented_runninglist.csv
Checking for duplicates of cdc-tracked lineage hex codes... 

  All CDC-tracked lineages have unique hex codes - go team! 

Checking for variants in the list of CDC-tracked variant list that are missing hex codes: 

   Hex codes are present for all CDC-tracked variants. Go team! 

The correction key is up to date with all withdrawn lineages.
Successfully produced the clinical lineage classification file! 

shape: (5_976, 7)
┌────────────────┬────────────────┬────────┬──────────┬────────────────┬────────────────┬──────────┐
│ lineage_extrac ┆ Description    ┆ status ┆ who_name ┆ doh_variant_na ┆ doh_variant_na ┆ hex_code │
│ ted            ┆ ---            ┆ ---    ┆ ---      ┆ me             ┆ me_tables      ┆ ---      │
│ ---            ┆ str            ┆ str    ┆ str      ┆ ---            ┆ ---            ┆ str      │
│ str            ┆                ┆        ┆          ┆ str            ┆ str            ┆          │
╞════════════════╪════════════════╪════════╪══════════╪════════════════╪════════════════╪══════════╡
│ A              ┆ One of the two ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ original       ┆        ┆          ┆                ┆                ┆          │
│                ┆ haplot…        ┆        ┆          ┆                ┆                ┆          │
│ A.1            ┆ USA lineage    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│ A.2            ┆ Mostly Spanish ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage now    ┆        ┆          ┆                ┆                ┆          │
│                ┆ inc…           ┆        ┆          ┆                ┆                ┆          │
│ A.2.2          ┆ Australian     ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage        ┆        ┆          ┆                ┆                ┆          │
│ A.2.3          ┆ Scottish       ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage        ┆        ┆          ┆                ┆                ┆          │
│ …              ┆ …              ┆ …      ┆ …        ┆ …              ┆ …              ┆ …        │
│ XGY            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ XFG.3, …       ┆        ┆          ┆                ┆                ┆          │
│ XGZ            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ XFG, QF…       ┆        ┆          ┆                ┆                ┆          │
│ XHA            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ TB.2, R…       ┆        ┆          ┆                ┆                ┆          │
│ XHB            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ PY.1.1,…       ┆        ┆          ┆                ┆                ┆          │
│ XHC            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ #FABFD2  │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ XFG.5.4…       ┆        ┆          ┆                ┆                ┆          │
└────────────────┴────────────────┴────────┴──────────┴────────────────┴────────────────┴──────────┘
```
✅ Completed: Step 3 — Generate clinical output

## Step 4 — Generate wastewater output
Command: `uv run main.py --workflow-type wastewater --lineage-list pull_hexcodes/final_augmented_runninglist.csv -o results/ww_lineage_classifications.csv`

STDOUT:
```
Hello from lineage-classification-cdc! 

lineage notes were pulled successfully. 

Lineage list with hexcodes sourced from pull_hexcodes/final_augmented_runninglist.csv
Checking for duplicates of cdc-tracked lineage hex codes... 

  All CDC-tracked lineages have unique hex codes - go team! 

Checking for variants in the list of CDC-tracked variant list that are missing hex codes: 

   Hex codes are present for all CDC-tracked variants. Go team! 

The correction key is up to date with all withdrawn lineages.
Successfully produced the wastewater lineage classification file! 

shape: (6_268, 7)
┌────────────────┬───────────────┬───────────┬──────────┬───────────────┬───────────────┬──────────┐
│ lineage_extrac ┆ Description   ┆ status    ┆ who_name ┆ doh_variant_n ┆ wastewater_va ┆ hex_code │
│ ted            ┆ ---           ┆ ---       ┆ ---      ┆ ame           ┆ riant_name    ┆ ---      │
│ ---            ┆ str           ┆ str       ┆ str      ┆ ---           ┆ ---           ┆ str      │
│ str            ┆               ┆           ┆          ┆ str           ┆ str           ┆          │
╞════════════════╪═══════════════╪═══════════╪══════════╪═══════════════╪═══════════════╪══════════╡
│ A              ┆ One of the    ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ #333333  │
│                ┆ two original  ┆           ┆          ┆               ┆               ┆          │
│                ┆ haplot…       ┆           ┆          ┆               ┆               ┆          │
│ A.1            ┆ USA lineage   ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ #333333  │
│ A.2            ┆ Mostly        ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ #333333  │
│                ┆ Spanish       ┆           ┆          ┆               ┆               ┆          │
│                ┆ lineage now   ┆           ┆          ┆               ┆               ┆          │
│                ┆ inc…          ┆           ┆          ┆               ┆               ┆          │
│ A.2.2          ┆ Australian    ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ #333333  │
│                ┆ lineage       ┆           ┆          ┆               ┆               ┆          │
│ A.2.3          ┆ Scottish      ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ #333333  │
│                ┆ lineage       ┆           ┆          ┆               ┆               ┆          │
│ …              ┆ …             ┆ …         ┆ …        ┆ …             ┆ …             ┆ …        │
│ MC.34          ┆ Withdrawn:    ┆ withdrawn ┆ N/A      ┆ unreportable  ┆ unreportable  ┆ #EEEEEE  │
│                ┆ Alias of      ┆           ┆          ┆               ┆               ┆          │
│                ┆ B.1.1.529.…   ┆           ┆          ┆               ┆               ┆          │
│ XFG.20         ┆ Withdrawn:    ┆ withdrawn ┆ N/A      ┆ unreportable  ┆ unreportable  ┆ #EEEEEE  │
│                ┆ C10615T       ┆           ┆          ┆               ┆               ┆          │
│                ┆ (didn't rea…  ┆           ┆          ┆               ┆               ┆          │
│ XFG.3.31.1     ┆ Withdrawn:    ┆ withdrawn ┆ N/A      ┆ unreportable  ┆ unreportable  ┆ #EEEEEE  │
│                ┆ only one      ┆           ┆          ┆               ┆               ┆          │
│                ┆ sequence h…   ┆           ┆          ┆               ┆               ┆          │
│ QW.2           ┆ Redesignated  ┆ withdrawn ┆ N/A      ┆ XFG           ┆ XFG           ┆ #4E6EA1  │
│                ┆ as XFG.5.4.2  ┆           ┆          ┆               ┆               ┆          │
│ unreportable   ┆ For variants  ┆           ┆ N/A      ┆ unreportable  ┆ unreportable  ┆ #eeeeee  │
│                ┆ Freyja        ┆           ┆          ┆               ┆               ┆          │
│                ┆ detected b…   ┆           ┆          ┆               ┆               ┆          │
└────────────────┴───────────────┴───────────┴──────────┴───────────────┴───────────────┴──────────┘
```
✅ Completed: Step 4 — Generate wastewater output

## Output validation
✅ Found expected file: `results/lineage_classifications.csv`
✅ `results/lineage_classifications.csv` passed validation.
Rows: 5976
Columns: 7
✅ Found expected file: `results/ww_lineage_classifications.csv`
✅ `results/ww_lineage_classifications.csv` passed validation.
Rows: 6268
Columns: 7

## SUMMARY
Pending lineage rows: 44
Approved rows: 19
Rejected rows: 25
Still pending review: 0
QA disagreements: 23
Clinical output rows: 5976
Wastewater output rows: 6268

## FINAL STATUS
✅ SUCCESS: Pipeline completed successfully.

Updated files:
- `pull_hexcodes/final_augmented_runninglist.csv`
- `pull_hexcodes/pending_additions.csv`
- `pull_hexcodes/qa_disagreements.csv`
- `results/lineage_classifications.csv`
- `results/ww_lineage_classifications.csv`
