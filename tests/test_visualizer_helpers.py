import builtins
import os

import pytest

from codegraph import vizualyzer


class DummyGraph:
    def __init__(self):
        self.edges = []
        self.nodes = []

    def add_edges_from(self, edges):
        self.edges.extend(edges)

    def add_node(self, node):
        self.nodes.append(node)


def test_process_module_in_graph_edges():
    graph = DummyGraph()
    module = "/path/to/mod.py"
    module_links = {"func": ["other.dep", "local"]}

    module_edges, sub_edges = vizualyzer.process_module_in_graph(module, module_links, graph)

    assert ("mod.py", "func") in module_edges
    assert ("func", "dep") in sub_edges
    assert ("func", "local") in sub_edges


def test_get_template_dir_and_read_file():
    template_dir = vizualyzer._get_template_dir()
    assert os.path.isdir(template_dir)

    content = vizualyzer._read_template_file("index.html")
    assert "STYLES_PLACEHOLDER" in content


def test_get_d3_html_template_replaces_placeholders():
    html = vizualyzer.get_d3_html_template({"nodes": [], "links": [], "unlinkedModules": []})
    assert "STYLES_PLACEHOLDER" not in html
    assert "GRAPH_DATA_PLACEHOLDER" not in html
    assert "\"nodes\": []" in html


def test_draw_graph_writes_file_and_opens_browser(tmp_path, monkeypatch):
    opened = {}

    def fake_open(url):
        opened["url"] = url
        return True

    monkeypatch.setattr(vizualyzer.webbrowser, "open", fake_open)

    output_path = tmp_path / "graph.html"
    vizualyzer.draw_graph({"/tmp/a.py": {"func": []}}, output_path=output_path.as_posix())

    assert output_path.exists()
    assert opened["url"].startswith("file://")


def test_draw_graph_matplotlib_missing_deps(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("matplotlib") or name.startswith("networkx"):
            raise ImportError("blocked")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ImportError):
        vizualyzer.draw_graph_matplotlib({"/tmp/a.py": {"func": []}})
