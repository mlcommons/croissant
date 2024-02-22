from unittest import mock

from etils import epath
import pandas as pd
import pytest

from core import files as files_module

FileTypes = files_module.FileTypes


@mock.patch.object(files_module, "guess_file_type", return_value=FileTypes.CSV)
def test_check_file_csv_url(guess_file_type):
    del guess_file_type
    csv = epath.Path(
        # This is the hash path for "https://my.url".
        "/tmp/croissant-editor-f76b4732c82d83daf858fae2cc0e590d352a4bceb781351243a03daab11f76bc"
    )
    # Test unescaped CSV
    if csv.exists():
        csv.unlink()
    with csv.open("w") as f:
        f.write("column1,column2\n")
        f.write("a,1\n")
        f.write("b,2\n")
        f.write("c,3\n")
    file = files_module.file_from_url("https://my.url", set(), epath.Path())
    pd.testing.assert_frame_equal(
        file.df, pd.DataFrame({"column1": ["a", "b", "c"], "column2": [1, 2, 3]})
    )

    # Test error thrown on no file
    csv.unlink()
    with pytest.raises(Exception):
        files_module.file_from_url("https://my.url", set(), epath.Path())

    # Test escaped CSV
    content = b'"This","Is"\n1,2\n3,4'
    with csv.open("wb") as f:
        f.write(content)
    file = files_module.file_from_url("https://my.url", set(), epath.Path())
    pd.testing.assert_frame_equal(file.df, pd.DataFrame({"This": [1, 3], "Is": [2, 4]}))


@mock.patch.object(files_module, "guess_file_type", return_value=FileTypes.TSV)
def test_check_file_tsv_url(guess_file_type):
    del guess_file_type
    tsv = epath.Path(
        # This is the hash path for "https://my.url".
        "/tmp/croissant-editor-f76b4732c82d83daf858fae2cc0e590d352a4bceb781351243a03daab11f76bc"
    )
    # Test unescaped CSV
    if tsv.exists():
        tsv.unlink()
    with tsv.open("w") as f:
        f.write("column1\tcolumn2\n")
        f.write("a\t1\n")
        f.write("b\t2\n")
        f.write("c\t3\n")
    file = files_module.file_from_url("https://my.url", set(), epath.Path())
    pd.testing.assert_frame_equal(
        file.df, pd.DataFrame({"column1": ["a", "b", "c"], "column2": [1, 2, 3]})
    )

    # Test error thrown on no file
    tsv.unlink()
    with pytest.raises(Exception):
        files_module.file_from_url("https://my.url", set(), epath.Path())

    # Test escaped TSV
    content = b'"This"\t"Is"\n1\t2\n3\t4'
    with tsv.open("wb") as f:
        f.write(content)
    file = files_module.file_from_url("https://my.url", set(), epath.Path())
    pd.testing.assert_frame_equal(file.df, pd.DataFrame({"This": [1, 3], "Is": [2, 4]}))


@mock.patch.object(files_module, "guess_file_type", return_value="unknown")
def test_check_file_unknown(guess_file_type):
    del guess_file_type
    with pytest.raises(NotImplementedError):
        files_module.file_from_url("https://my.url", set(), epath.Path())
