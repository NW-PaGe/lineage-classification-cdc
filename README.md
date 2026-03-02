# lineage-classification-cdc
This repo contains code for generating the SARS-CoV-2 lineage classification files (clinical and wastewater flavors) used in WA DOH workflows.

## Purpose
The aim of this project is to provide a comprehensive mapping file for analyses involving SARS-CoV-2 lineages.

This allows:
- Mapping Pango lineages → CDC NowCast tracking groups
- Assigning official CDC hex color codes
- Assigning WHO variant labels
- Producing standardized lineage classification files used in WA DOH clinical and wastewater pipelines

## Repository Structure
Folder / File	Purpose

`main.py`	Generates lineage classification outputs

`pull_hexcodes/decision_tree.py`	Pulls CDC NowCast lineage list and manages approvals

`pull_hexcodes/final_augmented_runninglist.csv`	MASTER lineage approval file (source of truth)

`pull_hexcodes/pending_additions.csv`	New lineages requiring review

`who_hex_codes.csv`	WHO fallback color codes

`results/`	Output location

## Requirements
This repo uses uv for dependency management.

Install uv:
https://github.com/astral-sh/uv

Clone the repository:
```bash
git clone https://github.com/NW-PaGe/lineage-classification-cdc.git
cd lineage-classification-cdc
```
## Key Concept: Source of Truth
The file:

`pull_hexcodes/final_augmented_runninglist.csv` is the authoritative lineage list.
All outputs are generated from this file.
New CDC lineages must be approved before they propagate downstream.

## Weekly Update Workflow (CRITICAL)
This section documents the complete workflow required to update lineage classifications.

#### Step 1 — Pull latest repository updates
```
git checkout hexcode-pull-rework
git pull
```

#### Step 2 — Pull latest CDC NowCast lineage list
```
uv run pull_hexcodes/decision_tree.py
```
This produces:

| File               | Purpose                                                                                            |
| -------------------- |-------------------------------------------------------------------------------------------------- |
| `pending_additions.csv`  | New CDC lineages needing approval.  |
| `final_augmented_runninglist.csv`        | Updated lineage mapping.                                                  |
| `qa_disagreements.csv`             | Conflicts requiring manual review.|


#### Step 3 — Review and approve new lineages

Open: `pull_hexcodes/pending_additions.csv`
Approve by answering yes/no in `approve1 column of sheet. 
Save file. 

#### Step 4 — Apply Approvals
Run again:
```
uv run pull_hexcodes/decision_tree.py
```
This moves approved lineages into: `pull_hexcodes/final_augmented_runninglist.csv`

Approved lineages will NOT appear again in pending_additions.csv.

#### Step 5 — Generate clinical lineage classifications
Run:
```
uv run main.py \
  --workflow-type clinical \
  --lineage-list pull_hexcodes/final_augmented_runninglist.csv \
  -o results/lineage_classifications.csv
```
Output: `results/lineage_classifications.csv`

#### Step 6 — Generate wastewater lineage classifications
Run:
```
uv run main.py \
  --workflow-type wastewater \
  --lineage-list pull_hexcodes/final_augmented_runninglist.csv \
  -o results/ww_lineage_classifications.csv
```
Output: `results/ww_lineage_classifications.csv`

#### Step 7 — Commit updates
Run:
```
git add pull_hexcodes/final_augmented_runninglist.csv
git add pull_hexcodes/pending_additions.csv

git commit -m "Weekly CDC lineage update"

git push
```
GitHub Actions will regenerate downstream artifacts automatically.

#### Important Behavior
##### Pending additions do NOT repopulate after approval

Once a lineage is approved and added to `final_augmented_runninglist.csv` it becomes permanent and will not appear in `pending_additions.csv` again.

##### If a lineage is NOT approved

It will remain in `pending_additions.csv` until approved.

This prevents accidental propagation of unreviewed CDC lineage disaggregations.

## Running manually (quick reference)
Pull CDC updates:
```
uv run pull_hexcodes/decision_tree.py
```

Generate clinical:
```
uv run main.py \
  --workflow-type clinical \
  --lineage-list pull_hexcodes/final_augmented_runninglist.csv \
  -o results/lineage_classifications.csv
```

Generate wastewater:
```
uv run main.py \
  --workflow-type wastewater \
  --lineage-list pull_hexcodes/final_augmented_runninglist.csv \
  -o results/ww_lineage_classifications.csv
```
## Data Dictionary

The final product is a csv file that contains the following variables:

### Clinical File:
| Column               | Description                                                                                            |
| -------------------- |-------------------------------------------------------------------------------------------------- |
| `lineage_extracted`  | Canonical Pango lineage name as designated.  |
| `description`        | Lineage description from pango-designations repo                                                  |
| `status`             | One of **active/withdrawn** parsed from description or upstream field. Clinical file should contain only 'active' status lineages.|
| `doh_variant_name`   | The parent lineage bucket designated by CDC for tracking. If not descendant of a CDC-tracked lineage, who_name.               |
| `who_name`           | WHO label (Alpha…Omicron).                                                               |
| `hex_code`           | HEX color associated with `doh_ww_name` (CDC table preferred).                                     |
| `doh_variant_name_tables`     | Legacy variable used in a specific Wa DOH pipeline    |

### Wastewater File:
| Column               | Description                                                                                            |
| -------------------- |-------------------------------------------------------------------------------------------------- |
| `lineage_extracted`  | Canonical Pango lineage name as designated.  |
| `description`        | Lineage description from pango-designations repo                                                  |
| `status`             | One of **active/withdrawn** parsed from description or upstream field. Clinical file should contain only 'active' status lineages.|
| `doh_variant_name`   | The parent lineage bucket designated by CDC for tracking. If not descendant of a CDC-tracked lineage, who_name.               |
| `who_name`           | WHO label (Alpha…Omicron).                                                               |
| `hex_code`           | HEX color associated with `doh_ww_name` (CDC table preferred).                                     |
| `wastewater_variant_name` | Equivalent to doh_variant_name, but assigned either 'Ancestral' or 'Recombinant' where doh_variant_name == 'Other'.|
