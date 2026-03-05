import pytest
import polars as pl
from pango_corrector import pango_corrector

@pytest.fixture()
def corrector():
    corrector = pango_corrector.Corrector()
    return corrector

def test_init(corrector):
    headers = corrector.corrector_key.columns
    assert 'Lineage' in headers
    assert 'redesignation' in headers

def test_check_coverage(corrector,
                        capsys: pytest.CaptureFixture[str]):
    corrector.check_coverage()
    captured = capsys.readouterr()
    assert captured.out == "The correction key is up to date with all withdrawn lineages.\n"
    corrector.corrector_key = corrector.corrector_key.filter(pl.col("Lineage") != 'A.8')
    corrector.check_coverage()
    captured = capsys.readouterr()
    assert captured.out == "There are withdrawn lineages not accounted for in the correction key. Check the latest lineage_notes.txt file for ['A.8'] and update the correction key.\n"

def test_correct(corrector):
    corrector = pango_corrector.Corrector()
    assert corrector.correct('A.8') == 'A.9' # string input
    series_wrong = pl.Series("Lineage", ['A.8', 'A.10'])
    series_right = pl.Series("Lineage", ['A.9', 'A.5'])
    assert corrector.correct(series_wrong).equals(series_right)
    df_wrong = pl.DataFrame(series_wrong)
    df_right = pl.DataFrame(series_right)
    # test for error after neglecting to specify 'input_col'
    with pytest.raises(ValueError):
        corrector.correct(df_wrong)['redesignation']
    # test with dataframe input
    assert corrector.correct(df_wrong, input_col='Lineage')['redesignation'].equals(series_right)
    # test with list
    with pytest.raises(TypeError):
        corrector.correct(list(df_wrong))