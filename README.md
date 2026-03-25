# lineage-classification-cdc
This repo contains code for generating the SARS-CoV-2 lineage classification files (clinical and wastewater flavors) used in WA DOH workflows.

---

## Purpose
This project generates standardized lineage classification files by:

- Mapping Pango lineages → CDC NowCast tracking groups  
- Assigning CDC hex color codes  
- Assigning WHO variant labels  
- Producing clinical + wastewater lineage classification outputs  

---

## Repository Structure

| Path | Purpose |
|------|--------|
| `main.py` | Generates lineage classification outputs |
| `pull_hexcodes/decision_tree.py` | Pulls CDC NowCast data + manages approvals |
| `pull_hexcodes/final_augmented_runninglist.csv` | Source of Truth |
| `pull_hexcodes/pending_additions.csv` | New lineages needing review |
| `pull_hexcodes/qa_disagreements.csv` | Conflicts requiring review |
| `results/` | Output files (not committed) |

---

## Requirements

This repo uses `uv` for dependency management.

Install:
https://github.com/astral-sh/uv

Clone:
```bash
git clone https://github.com/NW-PaGe/lineage-classification-cdc.git
cd lineage-classification-cdc
```
## Key Concept: Source of Truth
The pipeline generates two primary output files:

- `results/lineage_classifications.csv (clinical)`
- `results/ww_lineage_classifications.csv (wastewater)`

- They are automatically generated and committed via GitHub Actions (or manually if running locally)

### Important
The `results/` directory must exist prior to running the pipeline
If running locally, create it with:
```
mkdir -p results
```  
## Weekly Update Workflow
This section documents the complete workflow required to update lineage classifications on a weekly basis.

#### Step 1 — Start from main
```
git checkout main
git pull origin main
```
#### Step 2- Create a branch for your updates
```
git checkout -b weekly-hex-update-YYYY-MM-DD
```
#### Step 3 — Pull latest CDC NowCast lineage list
```
uv run pull_hexcodes/decision_tree.py
```
This produces:

| File               | Purpose                                                                                            |
| -------------------- |-------------------------------------------------------------------------------------------------- |
| `pull_hexcodes/pending_additions.csv`  | New CDC lineages needing approval.  |
| `pull_hexcodes/final_augmented_runninglist.csv`        | Updated lineage mapping.                                                  |
| `pull_hexcodes/qa_disagreements.csv`             | Conflicts requiring manual review.|


#### Step 4 — Review and approve new lineages

Open: `pull_hexcodes/pending_additions.csv`
Approve by answering yes/no in `approve1 column of sheet. 
Save file. 

#### Step 5 — Apply Approvals
Run again:
```
uv run pull_hexcodes/decision_tree.py
```
This moves approved lineages into: `pull_hexcodes/final_augmented_runninglist.csv`

Approved lineages will NOT appear again in pending_additions.csv.

#### Step 6 — Generate clinical output
Run:
```
uv run main.py \
  --workflow-type clinical \
  --lineage-list pull_hexcodes/final_augmented_runninglist.csv \
  -o results/lineage_classifications.csv
```

#### Step 7 — Generate wastewater lineage classifications
Run:
```
uv run main.py \
  --workflow-type wastewater \
  --lineage-list pull_hexcodes/final_augmented_runninglist.csv \
  -o results/ww_lineage_classifications.csv
```

#### Step 8 — Commit required files
Run:
```
git add pull_hexcodes/decision_tree.py
git add pull_hexcodes/final_augmented_runninglist.csv
git add pull_hexcodes/pending_additions.csv
git add pull_hexcodes/qa_disagreements.csv
git add results/lineage_classifications.csv
git add results/ww_lineage_classifications.csv

git commit -m "Weekly CDC lineage update"
git push origin weekly-hex-update-YYYY-MM-DD
```
GitHub Actions will regenerate downstream artifacts automatically.

#### Step 9 — Open Pull Request
- Go to GitHub
- Open PR → main
- Tag reviewer(s) (Pauline and Dan)

#### Step 10 — After Merge
After your merge has been successful, run this locally: 
```
git checkout main
git pull origin main
git branch -d weekly-hex-update-YYYY-MM-DD
```

#### Important Rules
##### Do NOT Commit:
- `pull_hexcodes/retired/`
- `nowcast_workbook.twb`
  
##### Pending behavior:
- Approved → moves to running list → NEVER appears again
- Not approved → stays in pending

##### Automation Rules:
- Automation is safe ONLY if:
  - pending_additions.csv has no unapproved rows
  - qa_disagreements.csv is empty
- Otherwise → human review required

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
