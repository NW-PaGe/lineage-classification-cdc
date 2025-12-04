import polars as pl
from pango_corrector import pango_corrector
from pango_aliasor.aliasor import Aliasor

##########################################
### Define functions for use in main() ###
##########################################

def add_status(notes: pl.DataFrame):
    """add status column, where:
    lineages beginning with '*' are named withdrawn,
    otherwise are named active"""
    return notes.with_columns(
        pl.when(pl.col("lineage_extracted").str.starts_with("*"))
        .then(pl.lit("withdrawn"))
        .otherwise(pl.lit("active"))
        .alias("status")
    )

def remove_leading_stars(notes_status):
    """remove leading stars from the withdrawn lineage names"""
    return notes_status.with_columns(
        pl.when(pl.col("lineage_extracted").str.starts_with("*"))
        .then(pl.col("lineage_extracted").str.slice(1, None))
        .otherwise(pl.col("lineage_extracted"))
    )

def expand_lineages(df: pl.DataFrame,
                    col: str, 
                    output_col: "str", 
                    cond_col: str = None, 
                    cond_val: str = None):
    """
    expand lineages in the column 'col'
    when column 'cond_col' equals 'conv_val'
    """
    aliasor=Aliasor()
    if isinstance(cond_col, str) and isinstance(cond_val, str):
        expanded = df.with_columns(
        pl.when(pl.col(cond_col) == cond_val)
        .then(pl.col(col))
        .map_elements(aliasor.uncompress)
        .alias(output_col)
        )
        print(f"the values in ", col, "where ", cond_col, "= ", cond_val, "were expanded and assigned to ", output_col)
        return expanded
    else:
        expanded = df.with_columns(
        pl.col(col)
        .map_elements(aliasor.uncompress)
        .alias(output_col)
        )
        print(f"Lineages in column ", col, "were expanded and assigned to ", output_col)
        return expanded

def compress_lineages(df: pl.DataFrame,
                    col: str, 
                    output_col: "str", 
                    cond_col: str = None, 
                    cond_val: str = None):
    """
    compress lineages in the column 'col'
    when column 'cond_col' equals 'conv_val'
    """
    aliasor=Aliasor()
    if isinstance(cond_col, str) and isinstance(cond_val, str):
        compressed = df.with_columns(
        pl.when(pl.col(cond_col) == cond_val)
        .then(pl.col(col))
        .map_elements(aliasor.compress)
        .alias(output_col)
        )
        print("the values in ", col, "where ", cond_col, "= ", cond_val, "were compressed and assigned to ", output_col)
        return compressed
    else:
        compressed = df.with_columns(
        pl.col(col)
        .map_elements(aliasor.compress)
        .alias(output_col)
        )
        print("Lineages in column ", col, "were compressed and assigned to ", output_col)
        return compressed

def add_query_lineage(df: pl.DataFrame):
    """
    make a unity column containing the lineage
    - if there isn't a redesignation, use the expanded lineage_extracted
    - if there was a correction to withdrawn, use the redesignation 
    """
    return df.with_columns(
    pl.when(pl.col("status_target").is_null())
    .then("lineage_expanded")
    .otherwise(pl.col("status_target"))
    .alias("query_lineage")
    )

def best_parent(child_df: str,
                    child_col: str,
                    parents_df: pl.DataFrame, 
                    parents_col: str,
                    output_col: str):
    """
    As a whole, best_parent will:
    - for each lineage:
    - search for query_lineages within unique tracked cdc_lineage strings
    - keep the longest search result 
    """
    # get unique cdc lineages tracked
    cdc_unique = parents_df[parents_col].to_list()
    # get all parent matches, store under "parent matches" column
    parents_df = child_df.with_columns(
        pl.col(child_col)
        .str.extract_many(cdc_unique, overlapping=True)
        .alias("parent_matches")
    )

    def keep_longest(list):
        """
        function to count breaks of each string in "parent matches"
        and return the longest one.
        """
        max_breaks = -1
        result_string = ""
        for s in list:
            breaks = s.count(".")
            if breaks > max_breaks:
                max_breaks = breaks
                result_string = s
        return result_string
    # apply the keep_longest function to the parent matches
    return parents_df.with_columns(
        pl.col("parent_matches")
        .map_elements(keep_longest)
        .alias(output_col)
    ).drop("parent_matches") #remove this to keep col with all parent matches

##############################################
### main workflow starts here. ###############
### numbers in comments correspond to steps ##
### in hackmd doc ############################
##############################################

def main():
    """
    main() contains the whole workflow, from downloading the latest lineage designations,
    correcting withdrawn lineages, de-aliasing lineage names, etc.
    """
    print("Hello from lineage-classification-cdc!")
    # get the latest lineage_notes.txt from pango-designation
    # Source: Official Pango lineage notes (tab-separated values) from the pango-designation GitHub repository
    lineage_notes_url = \
        'https://raw.githubusercontent.com/cov-lineages/pango-designation/refs/heads/master/lineage_notes.txt'
    notes = pl.read_csv(lineage_notes_url, separator='\t')
    lineage_notes = notes.rename({'Lineage': 'lineage_extracted'})
    
    # read in the list of cdc-tracked lineages
    with open("variants_unique.txt", 'r') as cdc_variants:
        cdc_variants = pl.read_csv(cdc_variants,
                    has_header=False,
                    new_columns=["cdc_lineage"],
                    separator="|")
    # read in the parsed hex codes from pull_hexcodes
    with open("pull_hexcodes/parsed_hexcodes.csv", 'r') as codes:
        parsed_hexcodes = pl.read_csv(codes)

    # read in the running list of hex codes for comparisons
    with open("hexcodes_RL.csv", 'r') as codes_RL:
        hexcodes_rl = pl.read_csv(codes_RL)   

    #####
    # 3 #
    #####

    with_status = add_status(lineage_notes)
    notes_sliced = remove_leading_stars(with_status)
    corrector = pango_corrector.Corrector() # initialize pango corrector with key
    corrector.check_coverage() # make sure the key is current
    notes_with_target = corrector.correct(notes_sliced, input_col="lineage_extracted").rename({"redesignation": "status_target"})
    notes_w_expanded_target = expand_lineages(
        notes_with_target,
        col = "status_target",
        cond_col = "status",
        cond_val="withdrawn",
        output_col="status_target"
    )

    #####
    # 2 #
    #####

    aliasor = Aliasor() #initialize pango_aliasor
    notes_w_expanded_lineages = expand_lineages(notes_w_expanded_target,
                            col="lineage_extracted",
                            cond_col="status",
                            cond_val="active",
                            output_col="lineage_expanded")

    #####
    # 4 #
    #####
    notes_expanded_united = add_query_lineage(notes_w_expanded_lineages).drop("status_target")
    
    #####
    # 5 #
    #####
    # expand list of CDC tracked lineages, if not already expanded
    cdc_variants_expanded = expand_lineages(df=cdc_variants,
                                            col = "cdc_lineage",
                                            output_col = "cdc_lineage_expanded")
    #####
    # 6 #
    #####

    # for the complete data set notes_expanded_inited
    # find the closest parent lineage in the expanded
    # cdc lineages
    parents_found = best_parent(child_df = notes_expanded_united,
                                child_col="query_lineage",
                                parents_df = cdc_variants_expanded,
                                parents_col = "cdc_lineage_expanded",
                                output_col = "cdc_parent_lineage")

    # compress the cdc parent lineages after matching
    cdc_parents_compressed = compress_lineages(parents_found, 
                                            col = "cdc_parent_lineage",
                                            output_col="cdc_parent_lineage")
    
    # add hex codes from parsed list
    hex_added = cdc_parents_compressed.join(
        parsed_hexcodes,
        left_on = "cdc_parent_lineage",
        right_on = "variant",
        how = "left"
    )
    # add hex codes from running list for validation
    hex_rl_added = hex_added.join(
        hexcodes_rl,
        left_on = "cdc_parent_lineage",
        right_on = "variant_RL",\
        how = "left"
    )
    
if __name__ == "__main__":
    main()