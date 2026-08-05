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
