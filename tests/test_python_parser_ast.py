from argparse import Namespace

import pytest

from codegraph.core import CodeGraph
from codegraph.parsers.python_parser import PythonParser


def _write(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_python_version():
    parser = PythonParser()
    assert parser._parse_python_version(None) == (3, None)
    assert parser._parse_python_version("2.7") == (2, 7)
    assert parser._parse_python_version("3.10") == (3, 10)
    assert parser._parse_python_version("nope") == (3, None)


def test_collect_imports_module_and_entity_aliases():
    parser = PythonParser()
    parser._module_names_set = {"module_b", "module_c"}
    source = """import module_b as mb
from module_b import foo as bar
from module_c import sub as sub_alias
"""
    tree = parser._parse_source(source, "test.py")
    imports = parser._collect_imports(tree)

    assert imports.module_aliases["mb"] == "module_b"
    assert imports.entity_aliases["bar"] == "module_b.foo"
    assert imports.entity_aliases["sub_alias"] == "module_c.sub"
    assert "module_b" in imports.module_imports
    assert "module_c" in imports.module_imports


def test_usage_graph_resolves_alias_calls(tmp_path):
    _write(
        tmp_path,
        "module_b.py",
        """def foo():\n    return 1\n""",
    )
    _write(
        tmp_path,
        "module_a.py",
        """import module_b as mb\nfrom module_b import foo as bar\n\ndef call_all():\n    mb.foo()\n    bar()\n""",
    )

    args = Namespace(paths=[tmp_path.as_posix()], language="python")
    usage_graph = CodeGraph(args).usage_graph()

    module_a_path = (tmp_path / "module_a.py").as_posix()
    deps = set(usage_graph[module_a_path]["call_all"])
    assert "module_b.foo" in deps
    assert f"module_b._" in usage_graph[module_a_path]["_"]


def test_class_inheritance_dependency(tmp_path):
    _write(
        tmp_path,
        "module_b.py",
        """class Base:\n    pass\n""",
    )
    _write(
        tmp_path,
        "module_a.py",
        """import module_b\n\nclass Child(module_b.Base):\n    pass\n""",
    )

    args = Namespace(paths=[tmp_path.as_posix()], language="python")
    usage_graph = CodeGraph(args).usage_graph()

    module_a_path = (tmp_path / "module_a.py").as_posix()
    deps = set(usage_graph[module_a_path]["Child"])
    assert "module_b.Base" in deps


def test_entity_metadata_line_counts(tmp_path):
    _write(
        tmp_path,
        "module_a.py",
        """def foo():\n    x = 1\n    return x\n""",
    )
    args = Namespace(paths=[tmp_path.as_posix()], language="python")
    code_graph = CodeGraph(args)
    metadata = code_graph.get_entity_metadata()

    module_a_path = (tmp_path / "module_a.py").as_posix()
    assert metadata[module_a_path]["foo"]["lines"] == 3


def test_get_lines_numbers(tmp_path):
    _write(
        tmp_path,
        "module_a.py",
        "\"\"\"module\"\"\"\n\ndef foo():\n    return 1\n\n\ndef bar():\n    return 2\n",
    )
    args = Namespace(paths=[tmp_path.as_posix()], language="python")
    code_graph = CodeGraph(args)
    lines = code_graph.get_lines_numbers()

    module_a_path = (tmp_path / "module_a.py").as_posix()
    assert lines[module_a_path]["foo"] == (3, 4)
    assert lines[module_a_path]["bar"] == (7, 8)


def test_deduplicate_preserves_order():
    parser = PythonParser()
    items = ["a", "b", "a", "c", "b"]
    assert parser._deduplicate(items) == ["a", "b", "c"]
