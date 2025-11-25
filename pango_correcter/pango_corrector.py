import polars as pl

class Corrector:
    """Class representing a the corrector set of functions with corrector df"""
    def __init__(self, corrector_file='correction_key.csv'):
        with open(corrector_file, 'r', encoding="utf-8") as file:
            self.corrector_key = pl.read_csv(file, columns=["Lineage", "redesignation"])

    def check_coverage(self):
        """
        Check to see if any withdrawn lineages have been added to the lineage_notes.txt.
        and report any that are not present in the corrector .csv.
        """
        print("Checking coverage for withdrawn lineages by the translation csv")
        lineage_notes_url = 'https://raw.githubusercontent.com/cov-lineages/pango-designation/refs/heads/master/lineage_notes.txt'
        notes = pl.read_csv(lineage_notes_url, separator='\t')
        withdrawn_notes = notes.filter(pl.col("Lineage").str.starts_with("*"))
        withdrawn_notes_srch = withdrawn_notes.with_columns(pl.col("Lineage").str.slice(1, None))
        withdrawn_join = withdrawn_notes_srch.join(self.corrector_key, on="Lineage", how="left")
        withdrawn_notin_key = withdrawn_join.filter(pl.col('redesignation')=='null')
        if withdrawn_notin_key.height > 0:
            print("There are withdrawn lineages not accounted for in the correction key. " \
            "Check the latest lineage_notes.txt file and update the correction key.")
            print(withdrawn_notin_key)
        else:
            print("The correction key is up to date with all withdrawn lineages.")


    def correct(self, input_value):
        """
        Input a withdrawn SARS-CoV-2 lineage and get the current lineage, if it exists.
        If the new lineage does not exist, it will report 'unreportable'.

        This function handles three types of inputs:
        - input: string; output: string
        - input: series; output: series
        - input: polars df; output: polars df with 'designations' column joined
        """

        # Case 1: input is a single string
        if isinstance(input_value, str):
            out = self.corrector_key.filter(pl.col("Lineage") == input_value)
            return out["redesignation"][0] if out.height > 0 else None

        # Case 2: input is a Polars Series → left join
        elif isinstance(input_value, pl.Series):
            temp = input_value.to_frame("Lineage")
            result = temp.join(
                self.corrector_key,
                on="Lineage",
                how="left"
            )
            return result["redesignation"]
        elif isinstance(input_value, pl.DataFrame):
        # Ensure the input dataframe *has* a Lineage column
            if "Lineage" not in input_value.columns:
                raise ValueError("DataFrame input must contain a 'Lineage' column.")

            return input_value.join(
                self.corrector_key,
                on="Lineage",
                how="left"
            )
        else:
            raise TypeError("input_value must be a string, a pl.Series, or a pl.dataframe")
