import pathlib

import pytest

from codegraph.utils import get_python_paths_list


def test_get_python_paths_list_error():
    with pytest.raises(ValueError) as e:
        get_python_paths_list("../codegraph/core.py")
        assert "does not exists" in str(e)


def test_get_python_paths_list():
    expected = list(
        map(
            lambda x: (pathlib.Path(__file__).parents[1] / "codegraph" / x).as_posix(),
            ["core.py", "parser.py", "utils.py", "vizualyzer.py", "main.py"],
        )
    )
    assert (
        get_python_paths_list(
            (pathlib.Path(__file__).parents[1] / "codegraph").as_posix()
        )
        == expected
    )
