"""Tests for package installation and basic usage without optional dependencies."""

import os
import tempfile


def test_import_codegraph():
    """Test that codegraph can be imported without matplotlib."""
    import codegraph

    assert codegraph.__version__ is not None


def test_import_core():
    """Test that core module can be imported without matplotlib."""
    from codegraph import core

    assert hasattr(core, "CodeGraph")


def test_import_vizualyzer():
    """Test that vizualyzer can be imported without matplotlib."""
    from codegraph import vizualyzer

    assert hasattr(vizualyzer, "draw_graph")
    assert hasattr(vizualyzer, "draw_graph_matplotlib")


def test_d3_visualization_without_matplotlib():
    """Test that D3.js visualization works without matplotlib installed."""
    from codegraph import vizualyzer

    test_data = {"/test/module1.py": {"func1": ["module2.func2"], "_": []}, "/test/module2.py": {"func2": [], "_": []}}

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        output_path = f.name

    try:
        vizualyzer.draw_graph(test_data, output_path=output_path)
        assert os.path.exists(output_path)

        with open(output_path, "r") as f:
            content = f.read()
            assert "graphData" in content
            assert "d3.js" in content or "d3.v7" in content
            assert "module1.py" in content
            assert "module2.py" in content
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_codegraph_on_itself_without_matplotlib():
    """Test that CodeGraph can analyze its own codebase without matplotlib."""
    from codegraph.core import CodeGraph
    from argparse import Namespace

    codegraph_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    codegraph_src = os.path.join(codegraph_path, "codegraph")

    args = Namespace(paths=[codegraph_src])
    cg = CodeGraph(args)

    graph = cg.usage_graph()
    assert len(graph) > 0

    metadata = cg.get_entity_metadata()
    assert len(metadata) > 0


def test_cli_help():
    """Test that CLI help works without matplotlib."""
    from click.testing import CliRunner
    from codegraph.main import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "codegraph" in result.output.lower() or "PATHS" in result.output
