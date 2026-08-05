# lineage-classification-cdc
This repo contains code for generating the SARS-CoV-2 lineage classification files (clinical and wastewater flavors) used in WA DOH workflows.

---

## Purpose
SARS-CoV-2 reporting is conducted on multiple levels of organization, from local health jurisdictions all the way up to the CDC. SARS-CoV-2 is also surveilled across both clinical and wastewater samples.

The pango lineage designations serve as the canonical, heirarchical nomenclature system for SARS-CoV-2 variant reporting across health jurisdictions and surveillance programs (wastewater/clinical). On the CDC NowCast dashboard, variants are aggregated into different levels of organization for the purposes of reporting. For example, emerging variants that reach a certain proportion of cases will be disaggregated and tracked separately, and these are visualized with the dendrogram on the NowCast page. 

The purpose of this workflow is to produce a primary mapping file that can be used for aggregating SARS-CoV-2 variant data at the same taxonomic levels as in the CDC NowCast. This file enables synchronization of variant data aggregation, so that reports can be compared directly, at the same level of taxonomic resolution. To further aid in this harmonization, the color hex codes used in the NowCast visualizations are scraped from the NowCast for use in data visualizations. For variants that aren't descended from pango lineages tracked by CDC, the WHO nomenclature serves as a fallback classification, and these are also assigned color hex codes.

---

## Repository Structure
Production of the lineage classification files is acheived via discrete python modules:

| Module | Function |
|------|--------|
| `pull_hexcodes/` | Scrapes CDC NowCast Tableau markup data to obtain lineages and color hex codes |
| `pango_corrector/` | Applies corrections to historical SARS-CoV-2 datasets with lineage designations that have been withdrawn or changed |
| `main.py` | Pulls current pango lineage designations, and results from `pull_hexcodes` to produce lineage mapping files |

This process is executed via the wrapper script `scripts/run_lineage_update.py`. Results are committed to the `results/` directory weekly to capture the most current pango lineage designations and CDC-tracked lineages and color hex codes.

## Outputs:

### Clinical File:
Two files are produced. The 'clinical' file provides the following variables:
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
This file contains alternative variables that are useful for analysis of wastewater variant data. Variables are:
| Column               | Description                                                                                            |
| -------------------- |-------------------------------------------------------------------------------------------------- |
| `lineage_extracted`  | Canonical Pango lineage name as designated.  |
| `description`        | Lineage description from pango-designations repo                                                  |
| `status`             | One of **active/withdrawn** parsed from description or upstream field. Clinical file should contain only 'active' status lineages.|
| `doh_variant_name`   | The parent lineage bucket designated by CDC for tracking. If not descendant of a CDC-tracked lineage, who_name.               |
| `who_name`           | WHO label (Alpha…Omicron).                                                               |
| `hex_code`           | HEX color associated with `doh_ww_name` (CDC table preferred).                                     |
| `wastewater_variant_name` | Equivalent to doh_variant_name, but assigned either 'Ancestral' or 'Recombinant' where doh_variant_name == 'Other'.|
---

## Using These Lineage Classification Files

If using python, read the files in directly using polars (substutute `pd` for `pl` if using `pandas`):
```python
## clinical file
lcf = pl.read_csv("https://raw.githubusercontent.com/NW-PaGe/lineage-classification-cdc/refs/heads/main/results/lineage_classifications.csv")
```
Using R:
```R
lcf <- read.csv("https://raw.githubusercontent.com/NW-PaGe/lineage-classification-cdc/refs/heads/main/results/lineage_classifications.csv")
```

