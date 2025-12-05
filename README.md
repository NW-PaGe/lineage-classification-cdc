# lineage-classification-cdc
code and script to map pango lineages to CDC parent lineages and their respective CDC designated hex codes

## Purpose
The aim of this project is to provide a comprehensive mapping file for analyses involving SARS-CoV-2 lineages. It is especially useful for aligning outputs with pango lineages being tracked by CDC. This makes synchronizing standard SARS-CoV-2 epidemiological reporting with the CDC Nowcast a breeze. Take your pango lineages, and map them to same taxonomic bins as the national-level reporting, with the same hex color codes used in the NowCast. Additionally, pango lineages can be mapped to WHO Variant of Concerns.

This repo includes modules with more general use cases, such as:
-  `pull_hexcodes` for scraping NowCast results.
- `pango_corrector` for updating withdrawn pango lineages to the most current redesignations.

## Requirements
This repo is structured as a python package, and uses `uv` to handle dependencies and virtual environments. `uv` is all that is required to run these analyses. See the [documentation](https://github.com/astral-sh/uv) for installation instructions.

## Run the Analysis
After installing `uv`, run the analysis from the main directory:

```bash
uv run main.py
```
## Output

### Data Dictionary

The final product is a csv file that contains the following variables:


| Column               | Type   | Meaning                                                                                            |
| -------------------- | ------ | -------------------------------------------------------------------------------------------------- |
| `lineage`            | chr    | Canonical Pango lineage name as designated.  |
| `description`        | chr | Free-text from `lineages.csv`                                                  |
| `status`             | chr    | One of **Active/Withdrawn/Renamed/Merged/Redesignated** parsed from description or upstream field. |
| `status_target`      | chr | If a lineage has been renamed, merged, or redesignated according to the official Pango notes, this field records the target lineage name it points to.                                              |
| `lineage_expanded`   | chr    | This is the alias-expanded form of the Pango lineage — a fully explicit version that resolves shorthand aliases like BA.2.86 or KP.2 into their base form (e.g., B.1.1.529.2.86…).                                                 |
| `query_lineage`      | chr    | The lineage actually used to match CDC: `status_target` or `lineage_expanded`. If the lineage was renamed, merged, or redesignated → use its new name (status_target) as the “query lineage.” Otherwise → use the expanded alias version.                     |
| `cdc_parent_lineage` | chr | CDC display lineage matched by walk-up (exact or ancestor).                                        |
| `doh_ww_name`        | chr    | Final WW bucket: CDC parent, or `Recombinant`/`Ancestral`.                               |
| `doh_variant_name`   | chr    | Legacy DOH bucket (first token of `lineage`); retained for backwards compatibility.                |
| `who_name`           | chr    | WHO label (Alpha…Omicron) or `N/A`.                                                                |
| `hex_code`           | chr    | HEX color associated with `doh_ww_name` (CDC table preferred).                                     |
| `is_recombinant`     | lgl    | TRUE if recombinant by head (`X…`) or text (“recombinant”).     |
