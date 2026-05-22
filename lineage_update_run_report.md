# Lineage Classification Update Run Report
Run time: 2026-05-22T12:53:19

This report records automation steps, warnings, validation checks, and required manual review actions.

## Step 1 — Pull latest CDC lineage updates
Command: `uv run pull_hexcodes/decision_tree.py`

STDOUT:
```
Downloading Tableau workbook…
Archived previous final_augmented_runninglist.csv -> /home/als6303/lineage-classification-cdc/pull_hexcodes/retired/final_augmented_runninglist_2026-05-22_9.csv
Loaded running list: 117 variants
Found new Tableau candidates: 43
Wrote /home/als6303/lineage-classification-cdc/pull_hexcodes/pending_additions.csv (43 rows; 24 awaiting approval)
Approved additions included: 19
Wrote /home/als6303/lineage-classification-cdc/pull_hexcodes/final_augmented_runninglist.csv (136 total variants)
Wrote /home/als6303/lineage-classification-cdc/pull_hexcodes/qa_disagreements.csv (FYI only; does not overwrite running list)
Run complete: 2026-05-22T12:53:21
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
- Rejected rows: 24
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
     BA.2  #9CCD67     #9CCC65
  BA.2.86  #D770EE     #D771F1
     BQ.1  #006064     #FFBE7D
   CH.1.1  #827717     #A0CBE8
     JN.1  #61018F     #660099
  JN.1.18  #4AF32F     #4DF230
JN.1.18.6  #D16F2C     #E16B1D
   KP.2.3  #628DE8     #E15759
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
Archived previous final_augmented_runninglist.csv -> /home/als6303/lineage-classification-cdc/pull_hexcodes/retired/final_augmented_runninglist_2026-05-22_10.csv
Loaded running list: 117 variants
Found new Tableau candidates: 43
Wrote /home/als6303/lineage-classification-cdc/pull_hexcodes/pending_additions.csv (43 rows; 24 awaiting approval)
Approved additions included: 19
Wrote /home/als6303/lineage-classification-cdc/pull_hexcodes/final_augmented_runninglist.csv (136 total variants)
Wrote /home/als6303/lineage-classification-cdc/pull_hexcodes/qa_disagreements.csv (FYI only; does not overwrite running list)
Run complete: 2026-05-22T12:53:23
```
✅ Completed: Step 2 — Apply approved lineage updates
✅ Found expected file: `pull_hexcodes/final_augmented_runninglist.csv`

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

shape: (5_893, 7)
┌────────────────┬────────────────┬────────┬──────────┬────────────────┬────────────────┬──────────┐
│ lineage_extrac ┆ Description    ┆ status ┆ who_name ┆ doh_variant_na ┆ doh_variant_na ┆ hex_code │
│ ted            ┆ ---            ┆ ---    ┆ ---      ┆ me             ┆ me_tables      ┆ ---      │
│ ---            ┆ str            ┆ str    ┆ str      ┆ ---            ┆ ---            ┆ str      │
│ str            ┆                ┆        ┆          ┆ str            ┆ str            ┆          │
╞════════════════╪════════════════╪════════╪══════════╪════════════════╪════════════════╪══════════╡
│ A              ┆ One of the two ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ original       ┆        ┆          ┆                ┆                ┆          │
│                ┆ haplot…        ┆        ┆          ┆                ┆                ┆          │
│ A.1            ┆ USA lineage    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│ A.2            ┆ Mostly Spanish ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage now    ┆        ┆          ┆                ┆                ┆          │
│                ┆ inc…           ┆        ┆          ┆                ┆                ┆          │
│ A.2.2          ┆ Australian     ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage        ┆        ┆          ┆                ┆                ┆          │
│ A.2.3          ┆ Scottish       ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage        ┆        ┆          ┆                ┆                ┆          │
│ …              ┆ …              ┆ …      ┆ …        ┆ …              ┆ …              ┆ …        │
│ XGU            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ XFG.5.2…       ┆        ┆          ┆                ┆                ┆          │
│ XGV            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ NW.1.2,…       ┆        ┆          ┆                ┆                ┆          │
│ XGW            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ NY.3.3,…       ┆        ┆          ┆                ┆                ┆          │
│ XGY            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ XFG.3, …       ┆        ┆          ┆                ┆                ┆          │
│ XGZ            ┆ Recombinant    ┆ active ┆ N/A      ┆ Other          ┆ Other          ┆ N/A      │
│                ┆ lineage of     ┆        ┆          ┆                ┆                ┆          │
│                ┆ XFG, QF…       ┆        ┆          ┆                ┆                ┆          │
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

shape: (6_188, 7)
┌────────────────┬───────────────┬───────────┬──────────┬───────────────┬───────────────┬──────────┐
│ lineage_extrac ┆ Description   ┆ status    ┆ who_name ┆ doh_variant_n ┆ wastewater_va ┆ hex_code │
│ ted            ┆ ---           ┆ ---       ┆ ---      ┆ ame           ┆ riant_name    ┆ ---      │
│ ---            ┆ str           ┆ str       ┆ str      ┆ ---           ┆ ---           ┆ str      │
│ str            ┆               ┆           ┆          ┆ str           ┆ str           ┆          │
╞════════════════╪═══════════════╪═══════════╪══════════╪═══════════════╪═══════════════╪══════════╡
│ A              ┆ One of the    ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ N/A      │
│                ┆ two original  ┆           ┆          ┆               ┆               ┆          │
│                ┆ haplot…       ┆           ┆          ┆               ┆               ┆          │
│ A.1            ┆ USA lineage   ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ N/A      │
│ A.2            ┆ Mostly        ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ N/A      │
│                ┆ Spanish       ┆           ┆          ┆               ┆               ┆          │
│                ┆ lineage now   ┆           ┆          ┆               ┆               ┆          │
│                ┆ inc…          ┆           ┆          ┆               ┆               ┆          │
│ A.2.2          ┆ Australian    ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ N/A      │
│                ┆ lineage       ┆           ┆          ┆               ┆               ┆          │
│ A.2.3          ┆ Scottish      ┆ active    ┆ N/A      ┆ Other         ┆ Ancestral     ┆ N/A      │
│                ┆ lineage       ┆           ┆          ┆               ┆               ┆          │
│ …              ┆ …             ┆ …         ┆ …        ┆ …             ┆ …             ┆ …        │
│ MC.34          ┆ Withdrawn:    ┆ withdrawn ┆ N/A      ┆ Other         ┆ Other         ┆ N/A      │
│                ┆ Alias of      ┆           ┆          ┆               ┆               ┆          │
│                ┆ B.1.1.529.…   ┆           ┆          ┆               ┆               ┆          │
│ XFG.20         ┆ Withdrawn:    ┆ withdrawn ┆ N/A      ┆ Other         ┆ Other         ┆ N/A      │
│                ┆ C10615T       ┆           ┆          ┆               ┆               ┆          │
│                ┆ (didn't rea…  ┆           ┆          ┆               ┆               ┆          │
│ XFG.3.31.1     ┆ Withdrawn:    ┆ withdrawn ┆ N/A      ┆ Other         ┆ Other         ┆ N/A      │
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
Rows: 5893
Columns: 7
✅ Found expected file: `results/ww_lineage_classifications.csv`
✅ `results/ww_lineage_classifications.csv` passed validation.
Rows: 6188
Columns: 7

## SUMMARY
Pending lineage rows: 43
Approved rows: 19
Rejected rows: 24
Still pending review: 0
QA disagreements: 22
Clinical output rows: 5893
Wastewater output rows: 6188

## FINAL STATUS
✅ SUCCESS: Pipeline completed successfully.

Updated files:
- `pull_hexcodes/final_augmented_runninglist.csv`
- `pull_hexcodes/pending_additions.csv`
- `pull_hexcodes/qa_disagreements.csv`
- `results/lineage_classifications.csv`
- `results/ww_lineage_classifications.csv`
