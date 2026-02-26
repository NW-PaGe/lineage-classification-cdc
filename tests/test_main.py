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
            notes = get_lineage_notes()
            assert "lineage_extracted" in notes.columns
            assert "status" in notes.columns
            assert "description" in notes.columns
        
        def test_get_lineage_notes_returns_pl_DataFrame():
            notes = get_lineage_notes()
            assert isinstance(notes, pl.DataFrame)

    def test_get_hex_codes_path():

        def test_get_hex_codes_path_returns_codes():
            codes = get_hex_codes_path()
            assert "variant" in codes.columns
            assert "hex_code" in codes.columns
        
    def test_clean_cdc_hex_codes():
        codes = pl.DataFrame({
            "variant": ["BA.1"],
            "hex_code": ["ABCDEF "]
            })
        clean_codes = clean_cdc_hex_codes(codes)
        assert "doh_variant_name" in clean_codes.columns
        assert "ABCDEF" in clean_codes['hex_code']
    
    def test_define_unique_cdc_variants():
        codes = pl.DataFrame({
            "variant": ["BA.1", "BA.2"],
            "hex_code": ["ABCDEF", "GHIJKL"]
            })
        cdc_vars = define_unique_cdc_variants(codes)
        assert ["BA.1", "BA.2"] in cdc_vars
        assert isinstance(cdc_vars, pl.Series)
    
    def test_read_who_hexcodes():
        who_codes = read_who_hexcodes()
        assert ["who_name", "hex_code"] in who_codes.columns
        assert isinstance(who_codes, pl.DataFrame)

    def test_qc_hex_codes():

        def test_qc_hex_codes_pass(capsys: pytest.CaptureFixture[str]):
            codes = pl.DataFrame({
                "variant": ["BA.1", "BA.2"],
                "hex_code": ["ABCDEF", "GHIJKL"]
            })
            qc_hex_codes(codes)
            captured = capsys.readouterr()
            assert captured == "   Hex codes are present for all CDC-tracked variants. Go team! \n"
        
        def test_qc_hex_codes_detects_dup_vars(capsys: pytest.CaptureFixture[str]):
            codes = pl.DataFrame({
                "variant": ["BA.1", "BA.1"],
                "hex_code": ["ABCDEF", "GHIJKL"]
            })
            qc_hex_codes(codes)
            captured = capsys.readouterr()
            assert "    Duplicates were found in the list of CDC hex codes. Duplicates will be removed, and first value kept: \n" in captured
            assert print(codes) in captured

        def test_qc_hex_codes_detects_missing_codes():
            codes = pl.DataFrame({
                "variant": ["BA.1", "BA.2"],
                "hex_code": ["ABCDEF", NULL]
            })
            qc_hex_codes(codes)
            captured = capsys.readouterr()
            assert " The following cdc-tracked variants are missing hex codes \n" in captured
            assert "BA.2" in captured