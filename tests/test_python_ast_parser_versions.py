import sys
from argparse import Namespace

import pytest

from codegraph.core import CodeGraph

try:
    import typed_ast.ast27 as ast27
except ImportError:  # pragma: no cover - optional dependency
    ast27 = None


@pytest.mark.skipif(ast27 is None, reason="typed_ast is required for Python 2 parsing")
def test_python2_6_parse_print_statement(tmp_path):
    module_path = tmp_path / "module_py2_6.py"
    module_path.write_text(
        """def foo():\n    print 'hi'\n""",
        encoding="utf-8",
    )
    args = Namespace(paths=[module_path.as_posix()], language="python", python_version="2.6")
    usage_graph = CodeGraph(args).usage_graph()

    assert module_path.as_posix() in usage_graph
    assert "foo" in usage_graph[module_path.as_posix()]


@pytest.mark.skipif(ast27 is None, reason="typed_ast is required for Python 2 parsing")
def test_python2_7_parse_exception_syntax(tmp_path):
    module_path = tmp_path / "module_py2_7.py"
    module_path.write_text(
        """def foo():\n    try:\n        raise Exception('x')\n    except Exception, e:\n        return str(e)\n""",
        encoding="utf-8",
    )
    args = Namespace(paths=[module_path.as_posix()], language="python", python_version="2.7")
    usage_graph = CodeGraph(args).usage_graph()

    assert module_path.as_posix() in usage_graph
    assert "foo" in usage_graph[module_path.as_posix()]


def test_python3_8_parse_walrus(tmp_path):
    module_path = tmp_path / "module_py3_8.py"
    module_path.write_text(
        """def foo(value):\n    if (n := value):\n        return n\n""",
        encoding="utf-8",
    )
    args = Namespace(paths=[module_path.as_posix()], language="python", python_version="3.8")
    usage_graph = CodeGraph(args).usage_graph()

    assert module_path.as_posix() in usage_graph
    assert "foo" in usage_graph[module_path.as_posix()]


@pytest.mark.skipif(
    tuple(sys.version_info[:2]) < (3, 10),
    reason="match/case parsing requires Python 3.10+ runtime",
)
def test_python3_10_parse_match_case(tmp_path):
    module_path = tmp_path / "module_py3_10.py"
    module_path.write_text(
        """def foo(value):\n    match value:\n        case 1:\n            return 1\n        case _:\n            return 0\n""",
        encoding="utf-8",
    )
    args = Namespace(paths=[module_path.as_posix()], language="python", python_version="3.10")
    usage_graph = CodeGraph(args).usage_graph()

    assert module_path.as_posix() in usage_graph
    assert "foo" in usage_graph[module_path.as_posix()]
