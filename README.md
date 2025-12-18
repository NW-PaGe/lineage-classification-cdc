# lineage-classification-cdc
This repo contains code for generating the SARS-CoV-2 lineage classification files (clinical and wastewater flavors) used in Wa DOH workflows. 

## Purpose
The aim of this project is to provide a comprehensive mapping file for analyses involving SARS-CoV-2 lineages. It is especially useful for aligning outputs with pango lineages being tracked by CDC. This makes synchronizing standard SARS-CoV-2 epidemiological reporting with the CDC Nowcast a breeze. Take your pango lineages, and map them to same taxonomic bins as the national-level reporting, with the same hex color codes used in the NowCast. Additionally, pango lineages can be mapped to WHO Variant of Concerns.

This repo includes modules with more general use cases, such as:
- `pull_hexcodes` for scraping NowCast results for CDC-tracked lineages and associated color hex codes.
- `pango_corrector` for updating withdrawn pango lineages to the most current redesignations.

## Requirements
This repo is structured as a python package, and uses `uv` to handle dependencies and virtual environments. `uv` is all that is required to run these analyses. See the [documentation](https://github.com/astral-sh/uv) for installation instructions.

Clone the repository:
```bash
git clone https://github.com/NW-PaGe/lineage-classification-cdc.git
```
## Run the Analysis

### Generate the Mapping File with BASH Command
After installing `uv`, run the analysis from the main directory.

For a short explanation of arguments:
```bash
uv run main.py --help
```
To generate the clinical lineage classification file in a csv format:
```bash
uv run main.py --workflow_type wastewater -o results/ww_lineage_classifications.csv
```
### Coming soon - import this project as a python library and have dataframes generated seamlessly within your python workflow.

## Output

When running `main.py` directly, outputs will appear where as specified by the `-o` flag at command line.

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