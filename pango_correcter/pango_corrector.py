class corrector:
    def __init__(self, corrector_file='correction_key.json'):
        import json
        with open(corrector_file, 'r') as file:
            file_data = json.load(file)
        self.corrector_dict = {}
        for column in file_data.keys():
            if type(file_data[column]) is list or file_data[column] == "":
                self.corrector_dict[column] = column
            else:
                self.corrector_dict[column] = file_data[column]
        
    def check_coverage(self):
        """
        Check to see if any withdrawn lineages have been added to the lineage_notes.txt, and report any
        that are not present in the corrector .json
        """
        import pandas as pd
        lineage_notes_url = 'https://raw.githubusercontent.com/cov-lineages/pango-designation/refs/heads/master/lineage_notes.txt'
        notes = pd.read_csv(lineage_notes_url, sep='\t')
        withdrawn = notes['Lineage'][notes['Lineage'].str.startswith('*')]
        for lineage in withdrawn:
            if lineage in self.corrector_dict:
                continue
            else:
                print(f"'{lineage[1:]}' not found in the corrector dictionary. Check lineage_notes.txt and add the appropriate key value pair to the corrector dictionary .json.")

    def correct(self, name):
        print(self.corrector_dict[name])
