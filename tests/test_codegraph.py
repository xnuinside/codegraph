import pathlib
from argparse import Namespace

from codegraph.core import CodeGraph


def test_main():
    module_path = (
        pathlib.Path(__file__).parents[0] / "test_data" / "vizualyzer.py"
    ).as_posix()
    args = Namespace(paths=[module_path])
    usage_graph = CodeGraph(args).usage_graph()
    excepted = {
        module_path: {
            "draw_graph": ["process_module_in_graph"],
            "process_module_in_graph": [],
        }
    }
    assert sorted(usage_graph) == sorted(excepted)
