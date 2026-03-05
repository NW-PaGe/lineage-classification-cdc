import polars as pl
from pango_aliasor.aliasor import Aliasor

def test_polar_aliasor():
    def test_polar_aliasor_without_conditions():
        """Test polar_aliasor without conditions applies function to all rows."""
        df = pl.DataFrame({"lineage": ["B.1.1.7", "B.1.351"]})
        result = polar_aliasor(
            df=df,
            col="lineage",
            output_col="lineage_compressed",
            func="compress"
        )
        assert "lineage_compressed" in result.columns
        assert result.shape[0] == 2


    def test_polar_aliasor_with_conditions():
        """Test polar_aliasor with conditions only applies function to matching rows."""
        df = pl.DataFrame({
            "lineage": ["B.1.1.7", "B.1.351"],
            "status": ["active", "withdrawn"]
        })
        result = polar_aliasor(
            df=df,
            col="lineage",
            output_col="lineage_expanded",
            func="uncompress",
            cond_col="status",
            cond_val="active"
        )
        assert "lineage_expanded" in result.columns
        assert result.shape[0] == 2


    def test_polar_aliasor_output_column_created():
        """Test that output column is created with correct name."""
        df = pl.DataFrame({"lineage": ["BA.1"]})
        result = polar_aliasor(
            df=df,
            col="lineage",
            output_col="new_lineage",
            func="compress"
        )
        assert "new_lineage" in result.columns


    def test_polar_aliasor_preserves_original_data():
        """Test that original dataframe columns are preserved."""
        df = pl.DataFrame({
            "lineage": ["B.1.1.7"],
            "other_col": ["value"]
        })
        result = polar_aliasor(
            df=df,
            col="lineage",
            output_col="compressed",
            func="compress"
        )
        assert "lineage" in result.columns
        assert "other_col" in result.columns


    def test_polar_aliasor_returns_dataframe():
        """Test that polar_aliasor returns a Polars DataFrame."""
        df = pl.DataFrame({"lineage": ["BA.1.1"]})
        result = polar_aliasor(
            df=df,
            col="lineage",
            output_col="result",
            func="compress"
        )
        assert isinstance(result, pl.DataFrame)

def test_best_parent():
    """Test best_parent function for matching lineages to CDC parents."""
    
    def test_best_parent_simple_match():
        """Test best_parent finds exact parent match."""
        child_df = pl.DataFrame({"lineage": ["B.1.1.7.1"]})
        parents_df = pl.DataFrame({"cdc_lineage": ["B.1.1.7"]})
        result = best_parent(
            child_df=child_df,
            child_col="lineage",
            parents_df=parents_df,
            parents_col="cdc_lineage",
            output_col="parent"
        )
        assert "parent" in result.columns
        assert result["parent"][0] == "B.1.1.7"

    def test_best_parent_longest_match():
        """Test best_parent selects longest (most specific) parent."""
        child_df = pl.DataFrame({"lineage": ["B.1.1.7.1.5"]})
        parents_df = pl.DataFrame({"cdc_lineage": ["B.1.1.7", "B.1.1.7.1"]})
        result = best_parent(
            child_df=child_df,
            child_col="lineage",
            parents_df=parents_df,
            parents_col="cdc_lineage",
            output_col="parent"
        )
        assert result["parent"][0] == "B.1.1.7.1"

    def test_best_parent_no_match():
        """Test best_parent returns empty string when no match found."""
        child_df = pl.DataFrame({"lineage": ["XEC.1"]})
        parents_df = pl.DataFrame({"cdc_lineage": ["B.1.1.7"]})
        result = best_parent(
            child_df=child_df,
            child_col="lineage",
            parents_df=parents_df,
            parents_col="cdc_lineage",
            output_col="parent"
        )
        assert result["parent"][0] == ""

    def test_best_parent_multiple_rows():
        """Test best_parent processes multiple child lineages."""
        child_df = pl.DataFrame({"lineage": ["B.1.1.7.1", "B.1.351.1"]})
        parents_df = pl.DataFrame({"cdc_lineage": ["B.1.1.7", "B.1.351"]})
        result = best_parent(
            child_df=child_df,
            child_col="lineage",
            parents_df=parents_df,
            parents_col="cdc_lineage",
            output_col="parent"
        )
        assert result.shape[0] == 2
        assert result["parent"][0] == "B.1.1.7"
        assert result["parent"][1] == "B.1.351"

    def test_best_parent_prevents_partial_match():
        """Test best_parent doesn't match BA.1.1 to BA.1.11."""
        child_df = pl.DataFrame({"lineage": ["BA.1.1"]})
        parents_df = pl.DataFrame({"cdc_lineage": ["BA.1.11"]})
        result = best_parent(
            child_df=child_df,
            child_col="lineage",
            parents_df=parents_df,
            parents_col="cdc_lineage",
            output_col="parent"
        )
        assert result["parent"][0] == ""

    def test_best_parent_preserves_dataframe():
        """Test best_parent preserves original columns."""
        child_df = pl.DataFrame({
            "lineage": ["B.1.1.7.1"],
            "other_col": ["value"]
        })
        parents_df = pl.DataFrame({"cdc_lineage": ["B.1.1.7"]})
        result = best_parent(
            child_df=child_df,
            child_col="lineage",
            parents_df=parents_df,
            parents_col="cdc_lineage",
            output_col="parent"
        )
        assert "lineage" in result.columns
        assert "other_col" in result.columns
        assert "parent" in result.columns

    def test_best_parent_returns_dataframe():
        """Test best_parent returns a Polars DataFrame."""
        child_df = pl.DataFrame({"lineage": ["BA.1"]})
        parents_df = pl.DataFrame({"cdc_lineage": ["B.1.1.529"]})
        result = best_parent(
            child_df=child_df,
            child_col="lineage",
            parents_df=parents_df,
            parents_col="cdc_lineage",
            output_col="parent"
        )
        assert isinstance(result, pl.DataFrame)

def test_make_map():

    def test_get_lineage_notes():

        def test_get_lineage_notes_returns_correct_headers():
            """test that get_lineage_notes returns the required columns"""
            notes = get_lineage_notes()
            assert "lineage_extracted" in notes.columns
            assert "status" in notes.columns
            assert "description" in notes.columns
        
        def test_get_lineage_notes_returns_pl_DataFrame():
            """test that get_lineage_notes returns a pl.DataFrame"""
            notes = get_lineage_notes()
            assert isinstance(notes, pl.DataFrame)

    def test_get_hex_codes_path():

        def test_get_hex_codes_path_returns_codes():
            """test that get_hex_codes reads in dataset"""
            codes = get_hex_codes_path()
            assert "variant" in codes.columns
            assert "hex_code" in codes.columns
        
    def test_clean_cdc_hex_codes():
        """test that clean_hex_codes strips extra spaces and changes column name"""
        codes = pl.DataFrame({
            "variant": ["BA.1"],
            "hex_code": ["ABCDEF "]
            })
        clean_codes = clean_cdc_hex_codes(codes)
        assert "doh_variant_name" in clean_codes.columns
        assert "ABCDEF" in clean_codes['hex_code']
    
    def test_define_unique_cdc_variants():
        """test that define_unique_cdc_variants pulls the variants as a pl.Series"""
        codes = pl.DataFrame({
            "variant": ["BA.1", "BA.2"],
            "hex_code": ["ABCDEF", "GHIJKL"]
            })
        cdc_vars = define_unique_cdc_variants(codes)
        assert ["BA.1", "BA.2"] in cdc_vars
        assert isinstance(cdc_vars, pl.Series)
    
    def test_read_who_hexcodes():
        """test that read_who_hexcodes reads in a useful dataset"""
        who_codes = read_who_hexcodes()
        assert ["who_name", "hex_code"] in who_codes.columns
        assert isinstance(who_codes, pl.DataFrame)

    def test_qc_hex_codes():

        def test_qc_hex_codes_pass(capsys: pytest.CaptureFixture[str]):
            """test that QC hex codes pass valid data set"""
            codes = pl.DataFrame({
                "variant": ["BA.1", "BA.2"],
                "hex_code": ["ABCDEF", "GHIJKL"]
            })
            qc_hex_codes(codes)
            captured = capsys.readouterr()
            assert captured == "   Hex codes are present for all CDC-tracked variants. Go team! \n"
        
        def test_qc_hex_codes_detects_dup_vars(capsys: pytest.CaptureFixture[str]):
            """test that hex code QC detects duplicate variants/hex codes"""
            codes = pl.DataFrame({
                "variant": ["BA.1", "BA.1"],
                "hex_code": ["ABCDEF", "GHIJKL"]
            })
            qc_hex_codes(codes)
            captured = capsys.readouterr()
            assert "    Duplicates were found in the list of CDC hex codes. Duplicates will be removed, and first value kept: \n" in captured
            assert print(codes) in captured

        def test_qc_hex_codes_detects_missing_codes():
            """test that hexcode QC detects missing codes"""
            codes = pl.DataFrame({
                "variant": ["BA.1", "BA.2"],
                "hex_code": ["ABCDEF", NULL]
            })
            qc_hex_codes(codes)
            captured = capsys.readouterr()
            assert " The following cdc-tracked variants are missing hex codes \n" in captured
            assert "BA.2" in captured

    def test_build_base_df():
        """Test build_base_df function for creating base classification dataframe."""
        
        def test_build_base_df_produces_required_columns():
            """Test build_base_df produces all required output columns."""
            # Mock lineage_notes as it would be returned from get_lineage_notes()
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7", "B.1.351", "*BA.1"],
                "Description": ["desc1", "desc2", "desc3"]
            })
            # Mock cdc_variants as it would be created
            cdc_variants = pl.DataFrame({
                "cdc_lineage": ["B.1.1.7", "B.1.351", "B.1.1.529"]
            })
            # Call build_base_df with mocked data
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert "lineage_extracted" in result.columns
            assert "status" in result.columns
            assert "doh_variant_name" in result.columns
            assert "who_greek" in result.columns
        
        def test_build_base_df_identifies_withdrawn():
            """Test build_base_df correctly identifies withdrawn lineages."""
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7", "*B.1.351"],
                "Description": ["active", "withdrawn"]
            })
            cdc_variants = pl.DataFrame({"cdc_lineage": ["B.1.1.7", "B.1.351"]})
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert result["status"][0] == "active"
            assert result["status"][1] == "withdrawn"
        
        def test_build_base_df_removes_asterisk():
            """Test build_base_df removes leading asterisk from withdrawn lineages."""
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["*B.1.351"],
                "Description": ["withdrawn"]
            })
            cdc_variants = pl.DataFrame({"cdc_lineage": ["B.1.351"]})
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert "*" not in result["lineage_extracted"][0]
        
        def test_build_base_df_assigns_cdc_parent():
            """Test build_base_df correctly assigns CDC parent lineages."""
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7.1"],
                "Description": ["child of B.1.1.7"]
            })
            cdc_variants = pl.DataFrame({"cdc_lineage": ["B.1.1.7"]})
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert result["cdc_parent_lineage"][0] == "B.1.1.7"
        
        def test_build_base_df_assigns_who_names():
            """Test build_base_df correctly assigns WHO Greek letter names."""
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "Description": ["Alpha variant"]
            })
            cdc_variants = pl.DataFrame({"cdc_lineage": ["B.1.1.7"]})
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert result["who_greek"][0] == "Alpha"
        
        def test_build_base_df_handles_omicron():
            """Test build_base_df assigns Omicron to XBB and B.1.1.529."""
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["XBB", "B.1.1.529"],
                "Description": ["omicron recombinant", "omicron"]
            })
            cdc_variants = pl.DataFrame({"cdc_lineage": ["XBB", "B.1.1.529"]})
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert result["who_greek"][0] == "Omicron"
            assert result["who_greek"][1] == "Omicron"
        
        def test_build_base_df_returns_dataframe():
            """Test build_base_df returns a Polars DataFrame."""
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "Description": ["test"]
            })
            cdc_variants = pl.DataFrame({"cdc_lineage": ["B.1.1.7"]})
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert isinstance(result, pl.DataFrame)
        
        def test_build_base_df_preserves_description():
            """Test build_base_df preserves description column."""
            lineage_notes = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "Description": ["Alpha-like variant"]
            })
            cdc_variants = pl.DataFrame({"cdc_lineage": ["B.1.1.7"]})
            result = build_base_df(lineage_notes, cdc_variants)
            
            assert "Description" in result.columns
    
    def test_add_clinical_variables():
        """Test add_clinical_variables function for clinical workflow."""
            
        def test_add_clinical_variables_filters_active_only():
            """Test that add_clinical_variables filters to only active lineages."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7", "B.1.351"],
                "status": ["active", "withdrawn"],
                "doh_variant_name": ["Alpha", "Beta"],
                "who_greek": ["Alpha", "Beta"],
                "cdc_parent_lineage": ["B.1.1.7", "B.1.351"],
                "query_lineage": ["B.1.1.7", "B.1.351"],
                "lineage_expanded": ["B.1.1.7", "B.1.351"],
                "Description": ["test1", "test2"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result.shape[0] == 1
            assert result["status"][0] == "active"
        
        def test_add_clinical_variables_creates_table_name_column():
            """Test that doh_variant_name_tables column is created."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "doh_variant_name_tables" in result.columns
        
        def test_add_clinical_variables_maps_who_to_pango():
            """Test that WHO Greek names are correctly mapped to Pango lineages."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result["doh_variant_name_tables"][0] == "B.1.1.7"
        
        def test_add_clinical_variables_fills_null_tables():
            """Test that null doh_variant_name_tables values are filled with doh_variant_name."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["BA.1"],
                "status": ["active"],
                "doh_variant_name": ["Omicron"],
                "who_greek": [None],
                "cdc_parent_lineage": [None],
                "query_lineage": ["BA.1"],
                "lineage_expanded": ["BA.1"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result["doh_variant_name_tables"][0] == "Omicron"
        
        def test_add_clinical_variables_adds_cdc_hex():
            """Test that CDC hex codes are added."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "hex_code" in result.columns
        
        def test_add_clinical_variables_coalesces_hex_codes():
            """Test that hex codes are coalesced from CDC and WHO sources."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result["hex_code"][0] is not None
        
        def test_add_clinical_variables_drops_unwanted_columns():
            """Test that lineage_expanded, query_lineage, cdc_parent_lineage are dropped."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "lineage_expanded" not in result.columns
            assert "query_lineage" not in result.columns
            assert "cdc_parent_lineage" not in result.columns
        
        def test_add_clinical_variables_renames_who_greek():
            """Test that who_greek column is renamed to who_name."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "who_name" in result.columns
            assert "who_greek" not in result.columns
        
        def test_add_clinical_variables_fills_nulls():
            """Test that null values are filled with 'N/A'."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["BA.1"],
                "status": ["active"],
                "doh_variant_name": ["Other"],
                "who_greek": [None],
                "cdc_parent_lineage": [None],
                "query_lineage": ["BA.1"],
                "lineage_expanded": ["BA.1"],
                "Description": [None]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "N/A" in result.to_series().to_list()
        
        def test_add_clinical_variables_returns_dataframe():
            """Test that add_clinical_variables returns a Polars DataFrame."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert isinstance(result, pl.DataFrame)
        
        def test_add_clinical_variables_preserves_description():
            """Test that Description column is preserved."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["Alpha variant"]
            })
            result = add_clinical_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "Description" in result.columns
            def test_add_wastewater_variables():
                """Test add_wastewater_variables function for wastewater workflow."""
    
    def test_add_wastewater_variables():

        def test_add_wastewater_variables_creates_recombinant():
            """Test that lineages starting with X are labeled as Recombinant."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["XBB"],
                "status": ["active"],
                "doh_variant_name": ["Other"],
                "who_greek": [None],
                "cdc_parent_lineage": [None],
                "query_lineage": ["XBB"],
                "lineage_expanded": ["XBB"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "wastewater_variant_name" in result.columns
            assert result["wastewater_variant_name"][0] == "Recombinant"
        
        def test_add_wastewater_variables_creates_ancestral():
            """Test that non-tracked lineages not starting with X are labeled as Ancestral."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.1"],
                "status": ["active"],
                "doh_variant_name": ["Other"],
                "who_greek": [None],
                "cdc_parent_lineage": [None],
                "query_lineage": ["B.1.1.1"],
                "lineage_expanded": ["B.1.1.1"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result["wastewater_variant_name"][0] == "Ancestral"
        
        def test_add_wastewater_variables_preserves_tracked():
            """Test that tracked variants keep their doh_variant_name."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result["wastewater_variant_name"][0] == "Alpha"
        
        def test_add_wastewater_variables_excludes_unreportable():
            """Test that unreportable lineages are not classified as Ancestral."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["unreportable"],
                "status": [""],
                "doh_variant_name": ["Other"],
                "who_greek": [None],
                "cdc_parent_lineage": [None],
                "query_lineage": ["unreportable"],
                "lineage_expanded": ["unreportable"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result["wastewater_variant_name"][0] == "Other"
        
        def test_add_wastewater_variables_adds_hex_codes():
            """Test that hex codes are added from CDC and WHO sources."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "hex_code" in result.columns
        
        def test_add_wastewater_variables_drops_unwanted_columns():
            """Test that temporary hex code columns and processing columns are dropped."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "cdc_hex" not in result.columns
            assert "who_hex" not in result.columns
            assert "lineage_expanded" not in result.columns
            assert "query_lineage" not in result.columns
            assert "cdc_parent_lineage" not in result.columns
        
        def test_add_wastewater_variables_renames_who_greek():
            """Test that who_greek column is renamed to who_name."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "who_name" in result.columns
            assert "who_greek" not in result.columns
        
        def test_add_wastewater_variables_fills_nulls():
            """Test that null values are filled with 'N/A'."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["XBB"],
                "status": ["active"],
                "doh_variant_name": ["Other"],
                "who_greek": [None],
                "cdc_parent_lineage": [None],
                "query_lineage": ["XBB"],
                "lineage_expanded": ["XBB"],
                "Description": [None]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert "N/A" in result.to_series().to_list()
        
        def test_add_wastewater_variables_adds_unreportable_row():
            """Test that unreportable row is appended with grey hex code."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result.shape[0] > 1
            unreportable_row = result.filter(pl.col("wastewater_variant_name") == "unreportable")
            assert unreportable_row.shape[0] == 1
            assert unreportable_row["hex_code"][0] == "#eeeeee"
        
        def test_add_wastewater_variables_returns_dataframe():
            """Test that add_wastewater_variables returns a Polars DataFrame."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7"],
                "status": ["active"],
                "doh_variant_name": ["Alpha"],
                "who_greek": ["Alpha"],
                "cdc_parent_lineage": ["B.1.1.7"],
                "query_lineage": ["B.1.1.7"],
                "lineage_expanded": ["B.1.1.7"],
                "Description": ["test"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert isinstance(result, pl.DataFrame)
        
        def test_add_wastewater_variables_processes_multiple_rows():
            """Test that multiple rows are processed correctly with different classifications."""
            base_df = pl.DataFrame({
                "lineage_extracted": ["B.1.1.7", "XBB", "B.1.1.1"],
                "status": ["active", "active", "active"],
                "doh_variant_name": ["Alpha", "Other", "Other"],
                "who_greek": ["Alpha", None, None],
                "cdc_parent_lineage": ["B.1.1.7", None, None],
                "query_lineage": ["B.1.1.7", "XBB", "B.1.1.1"],
                "lineage_expanded": ["B.1.1.7", "XBB", "B.1.1.1"],
                "Description": ["test1", "test2", "test3"]
            })
            result = add_wastewater_variables(base_df, hexcodes_cdc, hexcodes_who)
            assert result["wastewater_variant_name"][0] == "Alpha"
            assert result["wastewater_variant_name"][1] == "Recombinant"
            assert result["wastewater_variant_name"][2] == "Ancestral"