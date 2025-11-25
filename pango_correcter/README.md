# Pango corrector

## Purpose
This module is used to return the current names of withdrawn pango lineages in historic datasets. It's meant to be used alongside `pango_aliasor`, which is used to expand/contract lineage names and return parent lineages. `pango_corrector` picks up where `pango_aliasor` leaves off, by working only with withdrawn pango lineages and offering corrections. Lineages are reassigned only if there is a clear merge/reassignment/redesignation in the `lineage_notes.txt` file (see below).

## Inputs
- `correction_key.json` contains the key-value pairs of withdrawn-corrected lineages. This file is currently incomplete and is being filled in manually based on the descriptions column in `lineage_notes.txt`. 
- `lineage_notes.txt` is located in the [pango-designations](https://github.com/cov-lineages/pango-designation) repo, and contains lineage names, as well as descriptions in a .tsv format.
- outputs 

## Usage
```python3
from pango_corrector import corrector
#initialize with the correction key
corrector = corrector()
#check whether the correction key is up to date
corrector.check_coverage()
#get the updated lineage name for "A.8" (string input)
corrector.correct("A.8")
```

See test.py for additional use cases, including series and dataframe inputs.