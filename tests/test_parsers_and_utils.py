from argparse import Namespace

import pytest

from codegraph.parsers import available_languages, get_parser
from codegraph.parsers.base import BaseParser
from codegraph.utils import get_paths_list


class DummyParser(BaseParser):
    language = "dummy"

    def get_source_files(self, paths):
        return []

    def parse_files(self, paths_list):
        return {}

    def usage_graph(self, modules_data):
        return {}

    def get_entity_metadata(self, modules_data):
        return {}


def test_available_languages_contains_python_and_rust():
    langs = available_languages()
    assert "python" in langs
    assert "rust" in langs


def test_get_parser_returns_python_parser():
    parser = get_parser("python", args=Namespace())
    assert parser.language == "python"


def test_get_parser_unsupported_language():
    with pytest.raises(ValueError):
        get_parser("nope")


def test_base_parser_get_dependencies():
    parser = DummyParser()
    usage_graph = {
        "a.py": {"func": ["b.func", "c.other"], "_": []},
        "b.py": {"func": []},
    }

    deps = parser.get_dependencies(usage_graph, "a.py", 1)
    assert deps[1] == {"b.py", "c.py"}


def test_get_paths_list_multi_extension(tmp_path):
    (tmp_path / "a.py").write_text("", encoding="utf-8")
    (tmp_path / "b.txt").write_text("", encoding="utf-8")

    paths = get_paths_list(tmp_path.as_posix(), [".py", ".txt"])
    names = {p.split("/")[-1] for p in paths}
    assert names == {"a.py", "b.txt"}
