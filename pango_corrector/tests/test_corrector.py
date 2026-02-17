import pytest
import polars as pl
from pango_corrector import pango_corrector

def test_init():
    corrector = pango_corrector.Corrector()
    headers = corrector.corrector_key.columns
    assert 'Lineage' in headers
    assert 'redesignation' in headers

def test_check_coverage(capsys: pytest.CaptureFixture[str]):
    corrector = pango_corrector.Corrector()
    corrector.check_coverage()
    captured = capsys.readouterr()
    assert captured.out == "The correction key is up to date with all withdrawn lineages.\n"
    corrector.corrector_key = corrector.corrector_key.filter(pl.col("Lineage") != 'A.8')
    corrector.check_coverage()
    captured = capsys.readouterr()
    assert captured.out == "The correction key is up to date with all withdrawn lineages.\n"