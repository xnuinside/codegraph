from argparse import Namespace

from codegraph.core import CodeGraph
from codegraph.parser import Import, create_objects_array


def test_import_comma_separated_statement():
    source = """import os, sys

def func():
    os.path.join()
"""
    result = create_objects_array("test.py", source)
    imports = result[-1]
    assert isinstance(imports, Import)
    assert "os" in imports.modules
    assert "sys" in imports.modules


def test_usage_in_string_literal_is_not_dependency(tmp_path):
    module_path = tmp_path / "module_a.py"
    module_path.write_text(
        """def foo():
    return 1

def bar():
    print("foo() should not count")
    return "foo()"
""",
        encoding="utf-8",
    )

    args = Namespace(paths=[module_path.as_posix()])
    usage_graph = CodeGraph(args).usage_graph()

    assert "foo" not in usage_graph[module_path.as_posix()]["bar"]


def test_alias_leak_between_modules(tmp_path):
    module_b = tmp_path / "module_b.py"
    module_b.write_text(
        """def foo():
    return 1
""",
        encoding="utf-8",
    )

    module_a = tmp_path / "module_a.py"
    module_a.write_text(
        """import module_b as mb

def use_alias():
    return mb.foo()
""",
        encoding="utf-8",
    )

    module_c = tmp_path / "module_c.py"
    module_c.write_text(
        """import module_b

def bar():
    mb = object()
    return mb.foo()
""",
        encoding="utf-8",
    )

    args = Namespace(paths=[tmp_path.as_posix()])
    usage_graph = CodeGraph(args).usage_graph()

    module_c_path = module_c.as_posix()
    deps = usage_graph[module_c_path]["bar"]
    assert all("module_b" not in dep for dep in deps)
