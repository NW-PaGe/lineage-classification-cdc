from pango_corrector import Corrector
import polars as pl
corrector = Corrector() # initializing pulls the latest correction keys .json
corrector.check_coverage() # see if any lineages have been withdrawn since last update to the corrector dictionary

print("Test the corrector function with a single string input: \n")
str_new_lineage = corrector.correct("A.8")
print("Input: \n")
print("A.8")
print("Output: \n")
print(str_new_lineage)

print("\n Test the corrector function with a polars series: \n")
ser_old_lineage = pl.Series(["A.8", "A.10"])
ser_new_lineage = corrector.correct(ser_old_lineage)
print("--- \n OLD NAMES: \n ---")
print(ser_old_lineage)
print("--- \n NEW NAMES: \n ---")
print(ser_new_lineage)

print("Test the correcter with an polars df as input: \n")
old_lineage_df = pl.read_csv("corrector_test_data.csv")
print("input dataframe: \n")
print(old_lineage_df)
new_lineage_df = corrector.correct(old_lineage_df, input_col="lineage_extracted")
print("output dataframe: \n")
print(new_lineage_df)
