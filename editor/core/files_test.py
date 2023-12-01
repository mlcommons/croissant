from etils import epath
import pandas as pd
import pytest

from .files import file_from_url
from .files import FileTypes


def test_check_file_csv():
    csv = epath.Path(
        # This is the hash path for "https://my.url".
        "/tmp/croissant-editor-f76b4732c82d83daf858fae2cc0e590d352a4bceb781351243a03daab11f76bc"
    )
    if csv.exists():
        csv.unlink()
    with csv.open("w") as f:
        f.write("column1,column2\n")
        f.write("a,1\n")
        f.write("b,2\n")
        f.write("c,3\n")
    file = file_from_url(FileTypes.CSV, "https://my.url", set(), epath.Path())
    pd.testing.assert_frame_equal(
        file.df, pd.DataFrame({"column1": ["a", "b", "c"], "column2": [1, 2, 3]})
    )
    # Fails with unknown encoding_format:
    with pytest.raises(NotImplementedError):
        file_from_url("unknown", "https://my.url", set(), epath.Path())
