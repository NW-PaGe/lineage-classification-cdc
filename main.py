import polars as pl
import fastexcel
from pango_corrector import pango_corrector
from pango_aliasor.aliasor import Aliasor

##########################################
### Define functions for use in main() ###
##########################################

def polar_aliasor(df: pl.DataFrame,
                    col: str,
                    output_col: str,
                    func: str,
                    cond_col: str = None,
                    cond_val: str = None):
    """
    Wrapper function for using pango_aliasor across columns of polars DataFrames.
    expand lineages in the column 'col'
    when column 'cond_col' equals 'conv_val'
    function = "compress" or "uncompress" (see aliasor documentation).
    Might also work for other aliasor functions (UNTESTED though)
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
    ## add a trailing "." for each cdc variant,
    # i.e. to prevent BA.1.1 from matching BA.1.11
    cdc_unique_query = [l + "." for l in cdc_unique]
    # get all parent matches, store under "parent matches" column.
    #adding
    parents_df = child_df.with_columns(
        pl.concat_str(pl.col(child_col), pl.lit(".")) #add a trailing "." to query lineages
        .str.extract_many(cdc_unique_query, overlapping=True)
        .alias("parent_matches")
    )
    def keep_longest(list):
        """
        function to count breaks of each list of strings in "parent matches"
        and return the longest one.
        """
        max_breaks = -1
        result_string = ""
        for s in list:
            breaks = s.count(".")
            if breaks > max_breaks:
                max_breaks = breaks
                result_string = s
        return result_string[:-1] #remove trailing "." after search is done
    # apply the keep_longest function to the parent matches. This is for
    # selecting the most distal/specific cdc-tracked variant
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

def make_map(csv: str = None):
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

    # read in the parsed hex codes from pull_hexcodes - pending pull_hexcodes working well
    # with open("pull_hexcodes/parsed_hexcodes.csv", 'r') as codes:
    #     parsed_hexcodes = pl.read_csv(codes)

    # read in the running list of hex codes
    with open("Lineage_Color_Codes.xlsx", 'rb') as hex_codes:
        hexcodes_rl = pl.read_excel(hex_codes, 
                                    sheet_name="NowCast Running List", 
                                    columns = ["doh_variant_name", "who_name", "hex_code"],
                                    schema_overrides={"doh_variant_name": pl.String,
                                                      "who_name": pl.String,
                                                      "hex_code": pl.String})
        hexcodes_retired = pl.read_excel(hex_codes, 
                                         sheet_name="Retired Variants on NowCast", 
                                         columns = ["doh_variant_name", "who_name", "hex_code"],
                                         schema_overrides={"doh_variant_name": pl.String,
                                                      "who_name": pl.String,
                                                      "hex_code": pl.String})
    #concatenate and remove leading/trailing whitespace from excel file
    hexcodes_dirty = pl.concat([hexcodes_rl, hexcodes_retired], how="vertical_relaxed")
    hexcodes = hexcodes_dirty.with_columns(
        pl.col(pl.Utf8).str.strip_chars()
    )
    # break cdc hex codes and who hex codes into separate df's
    hexcodes_cdc = hexcodes.filter(
        pl.col("who_name").is_null()
    ).drop("who_name")
    hexcodes_who = hexcodes.filter(
        pl.col("who_name").is_not_null()
    ).drop("doh_variant_name")
    #################################
    ### Hex code quality control. ###
    #################################
    # If duplicate rows exist for a cdc lineage, then print 
    # the duplicates and filter out repeats.
    print(f"Checking for duplicates of cdc-tracked lineage hex codes... \n")
    cdc_hex_dups = hexcodes_cdc.filter(hexcodes_cdc["doh_variant_name"].is_duplicated())
    if cdc_hex_dups.shape[0] > 0 :
        print(f"Duplicates were found in the list of CDC hex codes. Duplicates will be removed, and first value kept: \n")
        print(cdc_hex_dups)
        hexcodes_cdc = hexcodes_cdc.unique(subset="doh_variant_name", keep="first")
    else: print(f"All CDC-tracked lineages have unique hex codes - go team! \n")

    # same QC step for who hex codes:
    print(f"Checking for duplicates of who-designation hex codes... \n")
    who_hex_dups = hexcodes_who.filter(hexcodes_who["who_name"].is_duplicated())
    if who_hex_dups.shape[0] > 0 :
        print(f"Duplicates were found in the list of who hex codes. Duplicates will be removed, and first value kept: \n")
        print(who_hex_dups)
        hexcodes_who = hexcodes_who.unique(subset="who_name", keep="first")
    else : print(f"All WHO lineages have unique hex codes - go team! \n")

    # check for CDC-tracked lineages that are missing hex codes:
    print(f"Checking for variants in the list of CDC-tracked variant list that are missing hex codes: \n")
    cdc_variants_missing_hex_codes = pl.DataFrame({
        "cdc_lineages": cdc_variants
    }).join(
        hexcodes_cdc,
        left_on="cdc_lineages",
        right_on="doh_variant_name",
        how="left"
    ).filter(
        "hex_code" == None
    )
    if cdc_variants_missing_hex_codes.shape[0] > 0 :
        print("The following cdc-tracked variants are missing hex codes \n",
              cdc_variants_missing_hex_codes)
    else: print("Hex codes are present for all CDC-tracked variants. Go team! \n")
    #####
    # 3 #
    #####
    # add status
    with_status = lineage_notes.with_columns(
        pl.when(pl.col("lineage_extracted").str.starts_with("*"))
        .then(pl.lit("withdrawn"))
        .otherwise(pl.lit("active"))
        .alias("status")
    )

    notes_sliced = with_status.with_columns(
            pl.when(pl.col("lineage_extracted").str.starts_with("*"))
            .then(pl.col("lineage_extracted").str.slice(1, None))
            .otherwise(pl.col("lineage_extracted"))
    )

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
    notes_expanded_united = notes_w_expanded_lineages.with_columns(
    pl.when(pl.col("status_target").is_null())
    .then("lineage_expanded")
    .otherwise(pl.col("status_target"))
    .alias("query_lineage")
    ).drop("status_target")

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
    who_temp = cdc_parents_compressed.filter(
        pl.col("status")=="active" # get rid of redesignated lineages to avoid dups going into the next join
    ).join_where(
        who_map_df,
        (pl.col("query_lineage") == (pl.col("who_lineage"))) | # where query lineage equals a pango lineage specifying a who name OR:
        (pl.col("query_lineage").str.starts_with(pl.col("who_lineage")+".")), # is under the parent lineage of a who-named variant 
    ).select("query_lineage", "who_greek") #keep only these columns

    ### join the temp dataframe back to the main one to get the greek names
    ### into the main working df
    who_names = cdc_parents_compressed.join(
        who_temp,
        on="query_lineage",
        how="left",
        coalesce = False,
        validate = "m:1" #make sure temp df has unique keys
    ).drop("query_lineage_right") #drop this column


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
    # shouldn't change since this is for backwards compatibility (notice lack of omicron defs). Specific
    # variable for a workflow at WA DOH.

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

    #add hex codes for cdc parent lineages
    print("shape_before_adding_pango_hexcodes", variant_name_tables.shape)
    cdc_hex_added = variant_name_tables.join(
        hexcodes_cdc,
        on = "doh_variant_name",
        how = "left",
        coalesce = False,
        validate = "m:1"
    ).drop("doh_variant_name_right").rename({"hex_code": "cdc_hex"})
    print("cdc_hex_added shape:", cdc_hex_added.shape)
    # Log warning for missing CDC parent lineage hex codes
    missing_cdc_hex = cdc_hex_added.filter(
        pl.col("cdc_parent_lineage").is_not_null() & pl.col("cdc_hex").is_null()
    )
    print(f"The following cdc-tracked parent lineages are missing hex codes in the external list (excel):",
          missing_cdc_hex["cdc_parent_lineage"].unique(),
          "Will add the relevant hex code for the who name instead.")
    # Add the who hex codes
    who_hex_added = cdc_hex_added.join(
        hexcodes_who,
        left_on= "doh_variant_name",
        how = "left",
        right_on="who_name",
        coalesce = False,
        validate="m:1"
    ).drop("who_name").rename({"hex_code": "who_hex"})
    # merge cdc and who hex codes to single column 
    hex_added = who_hex_added.with_columns(
         pl.coalesce("cdc_hex", "who_hex"
             ).alias("hex_code")
    ).drop(["who_hex", "cdc_hex"])

    final_df = hex_added#.fill_null("N/A")
    print(final_df)
    if csv is not None:
        final_df.write_csv(csv)

if __name__ == "__main__":
    lineage_classifications = make_map(csv="results/lineage_class_new.csv")
