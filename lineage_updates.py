import csv

def add_status_and_target(lineages_expanded, lineage_notes_status):
    with open(lineages_expanded, 'r', newline='') as in_csv, \
        open(lineage_notes_status, 'w', newline='') as out_csv:
        reader = csv.DictReader(in_csv, delimiter=',')
        fieldnames = reader.fieldnames + ['status', 'lin_updated']
        writer = csv.DictWriter(out_csv, delimiter=',', fieldnames=fieldnames)
        writer.writerow(fieldnames)
        for row in reader:
            rename = ['rename', 'alias', 'merge']
            if 'withdrawn' in row['Description'].lower() \
                and any(sub not in row['Description'].lower() for sub in rename):
                row['status'] = 'withdrawn'

                writer.writerow(row)

lineages_expanded = 'results/lineage_notes_expanded.csv'
lineage_notes_status = 'results/lineage_notes_status.csv'
add_status_and_target(lineages_expanded, lineage_notes_status)
