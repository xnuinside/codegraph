import pathlib

import pytest

from codegraph.utils import get_python_paths_list


def test_get_python_paths_list_error():
    with pytest.raises(ValueError) as e:
        get_python_paths_list("../codegraph/core.py")
        assert "does not exists" in str(e)


def test_get_python_paths_list():
    base_path = pathlib.Path(__file__).parents[1] / "codegraph"
    expected = [
        (base_path / x).as_posix()
        for x in ["core.py", "parser.py", "utils.py", "vizualyzer.py", "main.py"]
    ]
    result = get_python_paths_list(base_path.as_posix())
    assert sorted(result) == sorted(expected)
