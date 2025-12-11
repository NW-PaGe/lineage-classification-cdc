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

def polar_aliasor(df: pl.DataFrame,
                    col: str, 
                    output_col: str,
                    func: str,
                    cond_col: str = None, 
                    cond_val: str = None):
    """
    Wrapper function for using pango_aliasor across columns of polars dataframes.
    expand lineages in the column 'col'
    when column 'cond_col' equals 'conv_val'
    function = "compress" or "uncompress"
    """
    aliasor=Aliasor()
    if isinstance(cond_col, str) and isinstance(cond_val, str):
        expanded = df.with_columns(
        pl.when(pl.col(cond_col) == cond_val)
        .then(pl.col(col))
        .map_elements(getattr(aliasor, func))
        .alias(output_col)
        )
        print(f"the values in ", col, "where ", cond_col, "= ", cond_val, "were expanded and assigned to ", output_col)
        return expanded
    else:
        expanded = df.with_columns(
        pl.col(col)
        .map_elements(getattr(aliasor, func))
        .alias(output_col)
        )
        print(f"Lineages in column ", col, "were expanded and assigned to ", output_col)
        return expanded

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
##  main workflow starts here.              ##
##  numbers in comments correspond to steps ##
##  in hackmd doc                           ##
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
    notes_w_expanded_target = polar_aliasor(
        notes_with_target,
        col = "status_target",
        cond_col = "status",
        cond_val="withdrawn",
        func="uncompress",
        output_col="status_target"
    )

    #####
    # 2 #
    #####

    aliasor = Aliasor() #initialize pango_aliasor
    notes_w_expanded_lineages = polar_aliasor(notes_w_expanded_target,
                            col="lineage_extracted",
                            cond_col="status",
                            cond_val="active",
                            func="uncompress",
                            output_col="lineage_expanded")

    #####
    # 4 #
    #####
    notes_expanded_united = add_query_lineage(notes_w_expanded_lineages).drop("status_target")

    #####
    # 5 #
    #####
    # expand list of CDC tracked lineages, if not already expanded
    cdc_variants_expanded = polar_aliasor(df=cdc_variants,
                                            col = "cdc_lineage",
                                            func = "uncompress",
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
    # fill empty cdc_parent_lineage cells with 'null' for downstream logic
    parents_found = parents_found.with_columns(
        pl.col("cdc_parent_lineage").replace("", None)
    )

    # compress the cdc parent lineages after matching
    cdc_parents_compressed = polar_aliasor(parents_found, 
                                            col = "cdc_parent_lineage",
                                            func = "compress",
                                            output_col="cdc_parent_lineage")

    # add hex codes from parsed list
    # hex_added = cdc_parents_compressed.join(
    #     parsed_hexcodes,
    #     left_on = "cdc_parent_lineage",
    #     right_on = "variant",
    #     how = "left",
    #     coalesce = False
    # )

    # print(f"hex_added", hex_added.shape)
    # add hex codes from running list for validation
    hex_rl_added = cdc_parents_compressed.join(
        hexcodes_rl,
        left_on = "cdc_parent_lineage",
        right_on = "variant_RL",
        how = "left",
        coalesce = False,
        validate = "m:1"
    ).drop("variant_RL")

    # add WHO greek letter designations
    ## make the dictionary
    who_map = {
        "B.1.1.7": "Alpha",
        "B.1.351": "Beta",
        "B.1.1.28.1": "Gamma",
        "B.1.617.2": "Delta",
        "B.1.427": "Epsilon", 
        "B.1.429": "Epsilon",
        "B.1.1.28.2": "Zeta",
        "B.1.525": "Eta",
        "B.1.1.28.3": "Theta",
        "B.1.526": "Iota",
        "B.1.617.1": "Kappa",
        "B.1.1.1.37": "Lambda",
        "B.1.621": "Mu",
        "B.1.1.529": "Omicron",
        "XBB": "Omicron"}
    ## turn the dict into a polars dataframe
    who_map_df = pl.DataFrame({
        "who_lineage": list(who_map.keys()),
        "who_greek": list(who_map.values())
    })

    ## this next part is goofy. join_where() doesn't support left joins,
    ## so there is an inner join on query lineage, then that gets
    ## joined back to the main working dataframe (left join).

    ### get the greek name.
    who_temp = hex_rl_added.filter(
        pl.col("status")=="active" # get rid of redesignated lineages to avoid dups going into the next join
    ).join_where(
        who_map_df,
        (pl.col("query_lineage") == (pl.col("who_lineage"))) | # where query lineage equals a pango lineage specifying a who name OR:
        (pl.col("query_lineage").str.starts_with(pl.col("who_lineage")+".")), # is under the parent lineage of a who-named variant 
    ).select("query_lineage", "who_greek")

    ### join the temp dataframe back to the main one to get the greek names
    ### into the main working df
    who_names = hex_rl_added.join(
        who_temp,
        on="query_lineage",
        how="left",
        coalesce = False,
        validate = "m:1" #make sure temp df has unique keys
    ).drop("query_lineage_right")


    # add DOH variant name - cdc parent if exists.
    # if not a child of cdc parent lineage,
    # then who_greek
    doh_variant_name = who_names.with_columns(
        pl.when(pl.col("cdc_parent_lineage").is_not_null()) #if lineage has a cdc parent
        .then(pl.col("cdc_parent_lineage")) # doh_variant_name = cdc parent
        .when(pl.col("cdc_parent_lineage").is_null() & pl.col("who_greek").is_not_null()) # if no cdc parent, but has who name
        .then(pl.col("who_greek")) # then doh_variant_name = who green name
        .otherwise(pl.lit("Other")).alias("doh_variant_name") # otherwise assign "other"
    )

    # Add the doh_variant_name_tables thing. Reverse-engineered from the R script on the network drive.
    # shouldn't change since this is for backwards compatibility (notice lack of omicron defs).

    ## make the map:
    table_name_map = {
        "Delta": "B.1.617.2",
        "Alpha": "B.1.1.7",
        "Beta": "B.1.351",
        "Epsilon": "B.1.427 / B.1.429",
        "Eta": "B.1.525",
        "Iota": "B.1.526",
        "Kappa": "B.1.617.1",
        "Gamma": "P.1",
        "Mu": "B.1.621",
        "Zeta": "P.2"
    }
    table_map_df = pl.DataFrame({
        "who_greek": list(table_name_map.keys()),
        "doh_variant_name_tables": list(table_name_map.values())
    })
    ## Now join these on "who_greek" and call doh_variant_name_tables
    variant_name_tables_greek_to_pango = doh_variant_name.join(
        table_map_df,
        on="who_greek",
        how="left",
        coalesce = False,
        validate = "m:1" #make sure temp df has unique keys
    ).drop("who_greek_right")

    ## fill in the null values with doh_variant_name
    variant_name_tables = variant_name_tables_greek_to_pango.with_columns(
        pl.when(pl.col("doh_variant_name_tables").is_null())
        .then(pl.col("doh_variant_name"))
        .alias("doh_variant_name_tables")
    )
    variant_name_tables.write_csv("results/lineage_classifications.csv")
    print("All parsed and written to results/lineage_classifications.csv")

if __name__ == "__main__":
    main()