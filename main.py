import polars as pl
from pango_correcter import pango_corrector

def main():
    print("Hello from lineage-classification-cdc!")
    lineage_notes_url = 'https://raw.githubusercontent.com/cov-lineages/pango-designation/refs/heads/master/lineage_notes.txt'
    notes = pl.read_csv(lineage_notes_url, separator='\t')

    def add_status(notes = notes):
        notes_status = notes.with_columns(
            pl.when(pl.col("Lineage").str.starts_with("*"))
            .then(pl.lit("withdrawn"))
            .otherwise(pl.lit("active"))
            .alias("status")
        )
        return notes_status
    
    def correct_withdrawn_lineages(notes_status):
        correcter = pango_corrector.Corrector()
        notes_ = notes_status.with_columns(
            pl.when(pl.col("Lineage").str.starts_with("*"))
            .then(pl.col("Lineage").str.slice(1, None))
            .otherwise(pl.col("Lineage"))
        )
        print(notes_corrected)

    with_status = add_status()
    correct_withdrawn_lineages(with_status)

if __name__ == "__main__":
    main()
