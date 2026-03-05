#!/bin/bash
curl https://raw.githubusercontent.com/NW-PaGe/lineage_classifications/refs/heads/DOH-ALS6303-patch-13/data/lineage_classifications.csv > legacy.csv
curl https://raw.githubusercontent.com/NW-PaGe/lineage-classification-cdc/refs/heads/hexcode-pull-rework/lineage_class.csv?token=GHSAT0AAAAAADM22WN7HYP5Q7OBS522PK722NCFLRQ > new.csv
NOW=$(date +"%Y-%m-%d_%H-%M-%S")
diff legacy.csv new.csv | echo > "full_diff_$NOW.csv"
diff --brief legacy.csv new.csv | echo > "only_discrepancies_$NOW.csv"
echo "diff files were produced"
