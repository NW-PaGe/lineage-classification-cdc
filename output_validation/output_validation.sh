#!/bin/bash
NOW=$(date +"%Y-%m-%d")
mkdir $NOW
curl https://raw.githubusercontent.com/NW-PaGe/lineage_classifications/refs/heads/main/data/lineage_classifications.csv > $NOW/legacy_clinical.csv
curl https://raw.githubusercontent.com/NW-PaGe/lineage_classifications/refs/heads/main/data/ww_lineage_classifications.csv > $NOW/legacy_wastewater.csv

diff $NOW/legacy_clinical.csv ../lineage_class.csv | echo > $NOW/full_diff_clinical_$NOW.csv
diff --brief $NOW/legacy_clinical.csv ../lineage_class.csv | echo > $NOW/discrepancies_clinical_$NOW.csv
diff $NOW/legacy_wastewater.csv ../lineage_class_wastewater.csv | echo > $NOW/full_diff_wastewater_$NOW.csv
diff --brief $NOW/legacy_wastewater.csv ../lineage_class_wastewater.csv | echo > $NOW/discrepancies_wastewater_$NOW.csv
echo "diff files were produced in the $NOW directory"
