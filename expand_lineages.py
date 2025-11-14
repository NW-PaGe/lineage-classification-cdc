import csv
import argparse
from pango_aliasor.aliasor import Aliasor

def expand_lineages(lineage_notes_txt, lineage_notes_expanded):
    aliasor = Aliasor()
    with open(lineage_notes_txt, 'r', newline='') as in_txt, \
    open(lineage_notes_expanded, 'w', newline='') as out_expanded:
        reader = csv.DictReader(in_txt, delimiter='\t')
        fieldnames = reader.fieldnames + ['lineage_expanded']
        writer = csv.DictWriter(out_expanded, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            row['lineage_expanded']=aliasor.uncompress(row['Lineage'])
            writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='This script adds the expaned pango lineage name')
    parser.add_argument("--input", help='The raw lineage classification txt from pango_designation')
    parser.add_argument("--output", "-o",
                    help="The output file with the expanded lineage names appended")
    args=parser.parse_args()
    expand_lineages(args.input, args.output)
