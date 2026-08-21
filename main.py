import polars as pl
import fastexcel
import argparse
from pathlib import Path
from pango_corrector import pango_corrector
from pango_aliasor.aliasor import Aliasor

##########################################
### Define functions for use in main() ###
##########################################


def polar_aliasor(
    df: pl.DataFrame,
    col: str,
    output_col: str,
    func: str,
    cond_col: str = None,
    cond_val: str = None,
):
    """
    Wrapper function for using pango_aliasor across columns of polars DataFrames.
    expand lineages in the column 'col'
    when column 'cond_col' equals 'conv_val'
    function = "compress" or "uncompress" (see aliasor documentation).
    Might also work for other aliasor functions (UNTESTED though)
    """
    aliasor = Aliasor()
    if isinstance(cond_col, str) and isinstance(cond_val, str):
        expanded = df.with_columns(
            pl.when(pl.col(cond_col) == cond_val)
            .then(pl.col(col))
            .map_elements(getattr(aliasor, func))
            .alias(output_col)
        )
        return expanded
    else:
        expanded = df.with_columns(
            pl.col(col).map_elements(getattr(aliasor, func)).alias(output_col)
        )
        return expanded


def best_parent(
    child_df: str,
    child_col: str,
    parents_df: pl.DataFrame,
    parents_col: str,
    output_col: str,
):
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
    # adding
    parents_df = child_df.with_columns(
        pl.concat_str(
            pl.col(child_col), pl.lit(".")
        )  # add a trailing "." to query lineages
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
        return result_string[:-1]  # remove trailing "." after search is done

    # apply the keep_longest function to the parent matches. This is for
    # selecting the most distal/specific cdc-tracked variant
    return parents_df.with_columns(
        pl.col("parent_matches").map_elements(keep_longest).alias(output_col)
    ).drop("parent_matches")  # remove this to keep col with all parent matches


##############################################
##  main workflow starts here.              ##
##  numbers in comments correspond to steps ##
##  in hackmd doc                           ##
##############################################


def make_map(csv: str, workflow_type: str = "clinical", lineage_list: Path = 'pull_hexcodes/final_augmented_runninglist.csv'):
    """
    main() contains the whole workflow, from downloading the latest lineage designations,
    correcting withdrawn lineages, de-aliasing lineage names, etc.
    """
    # Helpful error messages:
    if not isinstance(workflow_type, str):
        raise TypeError(
            f"The workflow_type argument expected a string, but received an object of class {workflow_type.__class__}."
        )
    if workflow_type not in ["clinical", "wastewater"]:
        raise ValueError(
            "Error: workflow_type should be either 'clinical' or 'wastewater'. Please correct the argument."
        )

    print("Hello from lineage-classification-cdc! \n")

    def get_lineage_notes():
        # get the latest lineage_notes.txt from pango-designation
        # Source: Official Pango lineage notes (tab-separated values) from the pango-designation GitHub repository
        lineage_notes_url = "https://raw.githubusercontent.com/cov-lineages/pango-designation/refs/heads/master/lineage_notes.txt"
        notes = pl.read_csv(lineage_notes_url, separator="\t")
        print(f"lineage notes were pulled successfully. \n")
        return notes.rename({"Lineage": "lineage_extracted"})

    lineage_notes = get_lineage_notes()
    
    def get_hex_codes_path(lineage_list: 'Path'):
        line_list_path = Path(lineage_list)
        if line_list_path.is_file():
            cdc_hexcodes_dirty = pl.read_csv(line_list_path)
            print(f'Lineage list with hexcodes sourced from {lineage_list}')
            return cdc_hexcodes_dirty
        else: raise FileNotFoundError(f"The lineage list file {lineage_list} could not be found.")

    cdc_hexcodes_dirty = get_hex_codes_path(lineage_list)

    def clean_cdc_hex_codes(cdc_hexcodes_dirty):
        hexcodes_clean = cdc_hexcodes_dirty.with_columns(pl.col(pl.Utf8).str.strip_chars())
        hexcodes_cdc = hexcodes_clean.rename({
            "variant": "doh_variant_name"
        }).drop("source")
        return hexcodes_cdc
    hexcodes_cdc = clean_cdc_hex_codes(cdc_hexcodes_dirty)

    def define_unique_cdc_variants(hexcodes_cdc):
        cdc_variants = pl.DataFrame({ "cdc_lineage": hexcodes_cdc["doh_variant_name"] })
        return cdc_variants
    cdc_variants = define_unique_cdc_variants(hexcodes_cdc)

    def read_who_hexcodes():
        who_hexcodes_dirty = pl.read_csv("who_hex_codes.csv")
        hexcodes_who = who_hexcodes_dirty.with_columns(pl.col(pl.Utf8).str.strip_chars())
        return hexcodes_who
    hexcodes_who = read_who_hexcodes()

    def qc_hex_codes(hexcodes_cdc):
        """
        Hex code quality control.
        If duplicate rows exist for a cdc lineage, then print
        the duplicates and filter out repeats.
        """

        print("Checking for duplicates of cdc-tracked lineage hex codes... \n")
        cdc_hex_dups = hexcodes_cdc.filter(
            hexcodes_cdc["doh_variant_name"].is_duplicated()
        )
        if cdc_hex_dups.shape[0] > 0:
            print(
                "    Duplicates were found in the list of CDC hex codes. Duplicates will be removed, and first value kept: \n"
            )
            print(cdc_hex_dups)
            hexcodes_cdc = hexcodes_cdc.unique(subset="doh_variant_name", keep="first")
        else:
            print("  All CDC-tracked lineages have unique hex codes - go team! \n")

        # check for CDC-tracked lineages that are missing hex codes:
        print(
            "Checking for variants in the list of CDC-tracked variant list that are missing hex codes: \n"
        )
        cdc_variants_missing_hex_codes = (
            hexcodes_cdc.filter(pl.col("hex_code").is_null())
        )
        if cdc_variants_missing_hex_codes.shape[0] > 0:
            print(
                " The following cdc-tracked variants are missing hex codes \n",
                cdc_variants_missing_hex_codes,
                "\n",
            )
        else:
            print("   Hex codes are present for all CDC-tracked variants. Go team! \n")
    qc_hex_codes(hexcodes_cdc)

    def build_base_df():
        # add status
        with_status = lineage_notes.with_columns(
            pl.when(pl.col("lineage_extracted").str.starts_with("*"))
            .then(pl.lit("withdrawn"))
            .otherwise(pl.lit("active"))
            .alias("status")
        )
        # remove leading * from withdrawn lineages
        notes_sliced = with_status.with_columns(
            pl.when(pl.col("lineage_extracted").str.starts_with("*"))
            .then(pl.col("lineage_extracted").str.slice(1, None))
            .otherwise(pl.col("lineage_extracted"))
        )
        # update withdrawn lineages to current designations
        corrector = pango_corrector.Corrector()  # initialize pango corrector with key
        corrector.check_coverage()  # make sure the key is current
        notes_with_target = corrector.correct(
            notes_sliced, input_col="lineage_extracted"
        ).rename({"redesignation": "status_target"})
        notes_w_expanded_target = polar_aliasor(
            notes_with_target,
            col="status_target",
            cond_col="status",
            cond_val="withdrawn",
            func="uncompress",
            output_col="status_target",
        )

        aliasor = Aliasor()  # initialize pango_aliasor
        notes_w_expanded_lineages = polar_aliasor(
            notes_w_expanded_target,
            col="lineage_extracted",
            cond_col="status",
            cond_val="active",
            func="uncompress",
            output_col="lineage_expanded",
        )

        notes_expanded_united = notes_w_expanded_lineages.with_columns(
            pl.when(pl.col("status_target").is_null())
            .then("lineage_expanded")
            .otherwise(pl.col("status_target"))
            .alias("query_lineage")
        ).drop("status_target")

        # expand list of CDC tracked lineages, if not already expanded
        cdc_variants_expanded = polar_aliasor(
            df=cdc_variants,
            col="cdc_lineage",
            func="uncompress",
            output_col="cdc_lineage_expanded",
        )

        # for the complete data set notes_expanded_inited
        # find the closest parent lineage in the expanded
        # cdc lineages
        parents_found = best_parent(
            child_df=notes_expanded_united,
            child_col="query_lineage",
            parents_df=cdc_variants_expanded,
            parents_col="cdc_lineage_expanded",
            output_col="cdc_parent_lineage",
        )
        # fill empty cdc_parent_lineage cells with 'null' for downstream logic
        parents_found = parents_found.with_columns(
            pl.col("cdc_parent_lineage").replace("", None)
        )

        # compress the cdc parent lineages after matching
        cdc_parents_compressed = polar_aliasor(
            parents_found,
            col="cdc_parent_lineage",
            func="compress",
            output_col="cdc_parent_lineage",
        )

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
            "XBB": "Omicron",
        }
        ## turn the dict into a polars dataframe
        who_map_df = pl.DataFrame(
            {"who_lineage": list(who_map.keys()), "who_greek": list(who_map.values())}
        )

        ## this next part is goofy. join_where() doesn't support left joins,
        ## so there is an inner join on query lineage, then that gets
        ## joined back to the main working dataframe (left join).

        ### get the greek name.
        who_temp = (
            cdc_parents_compressed.filter(
                pl.col("status")
                == "active"  # get rid of redesignated lineages to avoid dups going into the next join
            )
            .join_where(
                who_map_df,
                (
                    pl.col("query_lineage") == (pl.col("who_lineage"))
                )  # where query lineage equals a pango lineage specifying a who name OR:
                | (
                    pl.col("query_lineage").str.starts_with(pl.col("who_lineage") + ".")
                ),  # is under the parent lineage of a who-named variant
            )
            .select("query_lineage", "who_greek")
        )  # keep only these columns

        ### join the temp dataframe back to the main one to get the greek names
        ### into the main working df
        who_names = cdc_parents_compressed.join(
            who_temp,
            on="query_lineage",
            how="left",
            coalesce=False,
            validate="m:1",  # make sure temp df has unique keys
        ).drop("query_lineage_right")  # drop this column

        # add DOH variant name - cdc parent if exists.
        # if not a child of cdc parent lineage,
        # then who_greek
        w_variant_names = who_names.with_columns(
            pl.when(
                pl.col("cdc_parent_lineage").is_not_null()
            )  # if lineage has a cdc parent
            .then(pl.col("cdc_parent_lineage"))  # doh_variant_name = cdc parent
            .when(
                pl.col("cdc_parent_lineage").is_null()
                & pl.col("who_greek").is_not_null()
            )  # if no cdc parent, but has who name
            .then(pl.col("who_greek"))  # then doh_variant_name = who green name
            .otherwise(pl.lit("Other"))
            .alias("doh_variant_name")  # otherwise assign "other"
        )
        # We have encountered situations where lineages exist as 'withdrawn' and 'active' within
        # lineage_notes.txt (I'm looking at you, HK.3.11). This step removes the 'withdrawn' row
        # for variants that are also in the 'active' set.
        def dedup_variants(w_variant_names):
            dups = w_variant_names.filter(pl.col("lineage_extracted").is_duplicated())
            to_remove=[]
            # get names of duplicate variants
            duped_vars = dups.select(pl.col("lineage_extracted").unique())["lineage_extracted"].to_list()
            for lin in duped_vars:
                status = dups.filter(pl.col("lineage_extracted") == lin)['status'].unique().to_list()
                if 'active' in status and 'withdrawn' in status:
                    to_remove.append(lin)
            return w_variant_names.filter(
                ~(
                    pl.col("status") == "withdrawn"
                ) | ~pl.col("lineage_extracted").is_in(to_remove)
            )
        return dedup_variants(w_variant_names)

    base_df = build_base_df()

    ###########################################################
    ##    Workflows diverge here. Based on args passed,      ##
    ##      Workflow will build on the base dataframe        ##
    ## to produce the clinical file or wastewater file.      ##
    ###########################################################
    def add_clinical_variables():
        base_df_filtered = base_df.filter(pl.col("status") == "active")
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
            "Zeta": "P.2",
        }
        table_map_df = pl.DataFrame(
            {
                "who_greek": list(table_name_map.keys()),
                "doh_variant_name_tables": list(table_name_map.values()),
            }
        )
        ## Now join these on "who_greek" and call doh_variant_name_tables
        variant_name_tables_greek_to_pango = base_df_filtered.join(
            table_map_df,
            on="who_greek",
            how="left",
            coalesce=False,
            validate="m:1",  # make sure temp df has unique keys
        ).drop("who_greek_right")

        ## fill in the null values with doh_variant_name
        variant_name_tables = variant_name_tables_greek_to_pango.with_columns(
            pl.when(pl.col("doh_variant_name_tables").is_null())
            .then(pl.col("doh_variant_name"))
            .alias("doh_variant_name_tables")
        )

        # add hex codes for cdc parent lineages

        cdc_hex_added = (
            variant_name_tables.join(
                hexcodes_cdc,
                on="doh_variant_name",
                how="left",
                coalesce=False,
                validate="m:1",
            )
            .drop("doh_variant_name_right")
            .rename({"hex_code": "cdc_hex"})
        )

        # Add the who hex codes
        who_hex_added = (
            cdc_hex_added.join(
                hexcodes_who,
                left_on="doh_variant_name",
                how="left",
                right_on="who_name",
                coalesce=False,
                validate="m:1",
            )
            .drop("who_name")
            .rename({"hex_code": "who_hex"})
        )
        # merge cdc and who hex codes to single column
        hex_coalesced = who_hex_added.with_columns(
            pl.coalesce("cdc_hex", "who_hex").alias("hex_code")
        ).drop(["who_hex", "cdc_hex"])
        # final processing
        return (
            hex_coalesced.drop(
                "lineage_expanded", "query_lineage", "cdc_parent_lineage"
            )
            .rename({"who_greek": "who_name"})
            .fill_null("N/A")
        )

    if workflow_type == "clinical":  # add variables specific to clinical file:
        clinical_df = add_clinical_variables()
        if csv is not None:
            clinical_df.write_csv(csv)
        print("Successfully produced the clinical lineage classification file! \n")
        return clinical_df

    def add_wastewater_variables():
        # adding ww_variant_name with the following if/else logic
        ww_variant_name = base_df.with_columns(
            pl.when(
                (pl.col("doh_variant_name") == "Other")  # when doh_variant_name = other
                & (pl.col("query_lineage").str.starts_with("X"))
            )  # and query lineage starts with X
            .then(pl.lit("Recombinant"))  # then assign as recombinant
            .when(
                (pl.col("doh_variant_name") == "Other")  # when doh_variant_name = other
                & (
                    pl.col("query_lineage") != "unreportable"
                )  # and isn't a failed reassignment of withdrawn lineage
                & ~(pl.col("query_lineage").str.starts_with("X"))
            )  # and doesn't start with X
            .then(pl.lit("Ancestral"))  # then assign as ancestral
            .otherwise(
                pl.col("doh_variant_name")
            )  # otherwise use value in doh_variant_name
            .alias("wastewater_variant_name")  # name the new column
        )

        # add hex codes for cdc parent lineages
        ww_cdc_hex_added = (
            ww_variant_name.join(
                hexcodes_cdc,
                left_on="wastewater_variant_name",
                right_on="doh_variant_name",
                how="left",
                coalesce=False,
                validate="m:1",
            )
            .drop("doh_variant_name_right")
            .rename({"hex_code": "cdc_hex"})
        )

        # Add the who hex codes
        ww_who_hex_added = (
            ww_cdc_hex_added.join(
                hexcodes_who,
                left_on="doh_variant_name",
                how="left",
                right_on="who_name",
                coalesce=False,
                validate="m:1",
            )
            .drop("who_name")
            .rename({"hex_code": "who_hex"})
        )
        # merge cdc and who hex codes to single column
        ww_hex_coalesced = ww_who_hex_added.with_columns(
            pl.coalesce("cdc_hex", "who_hex").alias("hex_code")
        )
        # final processing
        ww_df = (
            ww_hex_coalesced.drop(
                "who_hex",
                "cdc_hex",
                "lineage_expanded",
                "query_lineage",
                "cdc_parent_lineage",
            )
            .fill_null("N/A")
            .rename({"who_greek": "who_name"})
        )
        # add a row for watewater_variant_name = "unreportable" so that the unreportable Freyja outputs
        # get assigned the grey hex code
        unreportables = pl.DataFrame(
            {
                "lineage_extracted": "unreportable",
                "Description": "For variants Freyja detected below threshold",
                "status": "",
                "who_name": "N/A",
                "doh_variant_name": "unreportable",
                "wastewater_variant_name": "unreportable",
                "hex_code": "#eeeeee",
            }
        )
        return ww_df.extend(unreportables)

    if workflow_type == "wastewater":  # add wastewater-specific variables:
        wastewater_df = add_wastewater_variables()
        if csv is not None:
            wastewater_df.write_csv(csv)
        print("Successfully produced the wastewater lineage classification file! \n")
        return wastewater_df


if __name__ == "__main__":
    # parse arguments passed to main.py
    parser = argparse.ArgumentParser(
        description="This script creates the lineage classification file."
    )
    parser.add_argument("-o", help="The filepath for the csv output (not required.)")
    parser.add_argument(
        "--workflow-type",
        help="This must be a string equal to either 'clinical' or 'wastewater'. If not provided, defaults to 'clinical'",
    )
    parser.add_argument("--lineage-list",
                        help="Optional. This must be a path to a .csv file containing the list of pango lineages and hexcodes used for binning. Defaults to pull_hexcodes/final_augmented_runninglist.csv")
    args = parser.parse_args()
    # require a csv filepath when main.py run directly (-o flag)
    if args.o is None:
        raise TypeError(
            "The output filepath was not provided. Please provide the file path for the csv output using the -o flag."
        )
    if args.workflow_type is None:
        args.workflow_type = "clinical"
        print(
            "the workflow type was not specified with the --workflow_type flag. The clinical lineage "
            "classification file will be produced by default.\n"
        )
    if args.lineage_list is None:
        args.lineage_list = "pull_hexcodes/final_augmented_runninglist.csv"

    lineage_classifications = make_map(workflow_type=args.workflow_type, csv=args.o, lineage_list=args.lineage_list)

    print(lineage_classifications)
