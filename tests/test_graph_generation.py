"""Tests for graph generation functionality."""
import csv
import pathlib
import tempfile
from argparse import Namespace

from codegraph.core import CodeGraph
from codegraph.parser import create_objects_array, Import
from codegraph.vizualyzer import convert_to_d3_format, export_to_csv


TEST_DATA_DIR = pathlib.Path(__file__).parent / "test_data"


class TestImportParsing:
    """Tests for import parsing functionality."""

    def test_comma_separated_imports(self):
        """Test that comma-separated imports are parsed correctly."""
        source = """from package import module_a, module_b, module_c

def use_them():
    module_a.func()
    module_b.func()
"""
        result = create_objects_array("test.py", source)
        # Last item should be Import object
        imports = result[-1]
        assert isinstance(imports, Import)
        # Should have three separate imports
        assert "package.module_a" in imports.modules
        assert "package.module_b" in imports.modules
        assert "package.module_c" in imports.modules

    def test_simple_import(self):
        """Test simple import statement."""
        source = """import os

def func():
    os.path.join()
"""
        result = create_objects_array("test.py", source)
        imports = result[-1]
        assert isinstance(imports, Import)
        assert "os" in imports.modules

    def test_from_import_single(self):
        """Test from ... import single item."""
        source = """from os import path

def func():
    path.join()
"""
        result = create_objects_array("test.py", source)
        imports = result[-1]
        assert isinstance(imports, Import)
        assert "os.path" in imports.modules

    def test_import_with_alias(self):
        """Test import with alias."""
        source = """from package import module as m

def func():
    m.something()
"""
        result = create_objects_array("test.py", source)
        imports = result[-1]
        assert isinstance(imports, Import)
        # Should contain the original name with alias
        assert any("package.module" in imp for imp in imports.modules)

    def test_comma_imports_with_alias(self):
        """Test comma-separated imports with aliases."""
        source = """from package import a as x, b as y, c

def func():
    x.something()
    y.other()
    c.third()
"""
        result = create_objects_array("test.py", source)
        imports = result[-1]
        assert isinstance(imports, Import)
        # All three should be present
        assert len([i for i in imports.modules if "package." in i]) == 3

    def test_multiline_imports_with_parentheses(self):
        """Test multi-line imports with parentheses."""
        source = """from package.submodule import (
    ClassA,
    ClassB,
    function_c,
)

def func():
    ClassA()
"""
        result = create_objects_array("test.py", source)
        imports = result[-1]
        assert isinstance(imports, Import)
        assert "package.submodule.ClassA" in imports.modules
        assert "package.submodule.ClassB" in imports.modules
        assert "package.submodule.function_c" in imports.modules

    def test_class_inheritance_parsing(self):
        """Test that class inheritance is captured."""
        source = """
class Base1:
    pass

class Base2:
    pass

class Child(Base1, Base2):
    pass

class MultiLineInherit(
    Base1,
    Base2,
):
    pass
"""
        result = create_objects_array("test.py", source)
        classes = [c for c in result if hasattr(c, 'super')]

        child = next(c for c in classes if c.name == "Child")
        assert "Base1" in child.super
        assert "Base2" in child.super

        multi = next(c for c in classes if c.name == "MultiLineInherit")
        assert "Base1" in multi.super
        assert "Base2" in multi.super


class TestCodeGraphConnections:
    """Tests for CodeGraph connection detection."""

    def test_single_module_usage(self):
        """Test usage detection within a single module."""
        module_path = (TEST_DATA_DIR / "vizualyzer.py").as_posix()
        args = Namespace(paths=[module_path])
        usage_graph = CodeGraph(args).usage_graph()

        assert module_path in usage_graph
        assert "draw_graph" in usage_graph[module_path]
        assert "process_module_in_graph" in usage_graph[module_path]["draw_graph"]

    def test_unused_functions_present(self):
        """Test that unused functions are still in the graph."""
        module_path = (TEST_DATA_DIR / "module_c.py").as_posix()
        args = Namespace(paths=[module_path])
        usage_graph = CodeGraph(args).usage_graph()

        assert module_path in usage_graph
        # Both functions should be present even if not used
        assert "func_c1" in usage_graph[module_path]
        assert "func_c2" in usage_graph[module_path]


class TestD3FormatConversion:
    """Tests for D3.js format conversion."""

    def test_convert_simple_graph(self):
        """Test basic D3 format conversion."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": ["func_b"],
                "func_b": [],
            }
        }
        result = convert_to_d3_format(usage_graph)

        assert "nodes" in result
        assert "links" in result

        # Check nodes - entity IDs use format module.py:entity_name
        node_ids = [n["id"] for n in result["nodes"]]
        assert "module.py" in node_ids
        assert "module.py:func_a" in node_ids
        assert "module.py:func_b" in node_ids

        # Check links
        links = result["links"]
        assert len(links) > 0

    def test_convert_multi_module_graph(self):
        """Test D3 conversion with multiple modules."""
        usage_graph = {
            "/path/to/a.py": {
                "func_a": ["b.func_b"],
            },
            "/path/to/b.py": {
                "func_b": [],
            },
        }
        result = convert_to_d3_format(usage_graph)

        node_ids = [n["id"] for n in result["nodes"]]
        assert "a.py" in node_ids
        assert "b.py" in node_ids

        # Check module types
        module_nodes = [n for n in result["nodes"] if n["type"] == "module"]
        assert len(module_nodes) == 2

    def test_convert_empty_graph(self):
        """Test D3 conversion with empty graph."""
        usage_graph = {}
        result = convert_to_d3_format(usage_graph)

        assert result["nodes"] == []
        assert result["links"] == []

    def test_module_entity_links(self):
        """Test that module-entity links are created."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": [],
                "func_b": [],
            }
        }
        result = convert_to_d3_format(usage_graph)

        # Should have module-entity links
        module_entity_links = [
            link for link in result["links"] if link["type"] == "module-entity"
        ]
        assert len(module_entity_links) >= 2

    def test_dependency_links(self):
        """Test that dependency links are created."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": ["other_module.func_b"],
            },
            "/path/to/other_module.py": {
                "func_b": [],
            },
        }
        result = convert_to_d3_format(usage_graph)

        # Should have dependency links
        dep_links = [link for link in result["links"] if link["type"] == "dependency"]
        assert len(dep_links) >= 1

    def test_nodes_have_required_fields(self):
        """Test that all nodes have required fields."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": ["func_b"],
                "func_b": [],
            }
        }
        result = convert_to_d3_format(usage_graph)

        for node in result["nodes"]:
            assert "id" in node
            assert "type" in node
            # Module nodes should have collapsed field
            if node["type"] == "module":
                assert "collapsed" in node

    def test_links_have_required_fields(self):
        """Test that all links have required fields."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": ["func_b"],
                "func_b": [],
            }
        }
        result = convert_to_d3_format(usage_graph)

        for link in result["links"]:
            assert "source" in link
            assert "target" in link
            assert "type" in link


class TestCodeGraphOnItself:
    """Tests for running CodeGraph on the codegraph package itself."""

    def test_codegraph_on_itself(self):
        """Test that CodeGraph can analyze its own source code."""
        codegraph_path = pathlib.Path(__file__).parents[1] / "codegraph"
        args = Namespace(paths=[codegraph_path.as_posix()])
        usage_graph = CodeGraph(args).usage_graph()

        # Should have all modules
        module_names = [pathlib.Path(p).name for p in usage_graph.keys()]
        assert "core.py" in module_names
        assert "parser.py" in module_names
        assert "main.py" in module_names
        assert "vizualyzer.py" in module_names
        assert "utils.py" in module_names

    def test_main_core_connection(self):
        """Test that main.py -> core.py connection is detected."""
        codegraph_path = pathlib.Path(__file__).parents[1] / "codegraph"
        args = Namespace(paths=[codegraph_path.as_posix()])
        usage_graph = CodeGraph(args).usage_graph()

        # Find main.py path
        main_path = None
        for path in usage_graph.keys():
            if path.endswith("main.py"):
                main_path = path
                break

        assert main_path is not None
        assert "main" in usage_graph[main_path]

        # main function should use core.CodeGraph
        main_deps = usage_graph[main_path]["main"]
        assert any("core" in str(d) for d in main_deps)

    def test_core_parsers_connection(self):
        """Test that core.py -> parsers connection is detected."""
        codegraph_path = pathlib.Path(__file__).parents[1] / "codegraph"
        args = Namespace(paths=[codegraph_path.as_posix()])
        usage_graph = CodeGraph(args).usage_graph()

        # Find core.py path
        core_path = None
        for path in usage_graph.keys():
            if path.endswith("core.py"):
                core_path = path
                break

        assert core_path is not None
        assert "CodeGraph" in usage_graph[core_path]

        # CodeGraph class should use parsers.get_parser
        codegraph_deps = usage_graph[core_path]["CodeGraph"]
        assert any("parsers" in str(d) for d in codegraph_deps)


class TestCSVExport:
    """Tests for CSV export functionality."""

    def test_export_creates_file(self):
        """Test that export_to_csv creates a CSV file."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": ["func_b"],
                "func_b": [],
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        export_to_csv(usage_graph, output_path=output_path)

        assert pathlib.Path(output_path).exists()
        pathlib.Path(output_path).unlink()

    def test_export_has_correct_columns(self):
        """Test that CSV has all required columns."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": [],
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        export_to_csv(usage_graph, output_path=output_path)

        with open(output_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames

        expected_columns = ['name', 'type', 'parent_module', 'full_path', 'links_out', 'links_in', 'lines']
        assert fieldnames == expected_columns
        pathlib.Path(output_path).unlink()

    def test_export_module_data(self):
        """Test that module nodes are exported correctly."""
        usage_graph = {
            "/path/to/module.py": {
                "func_a": [],
            }
        }
        entity_metadata = {
            "/path/to/module.py": {
                "func_a": {"lines": 10, "entity_type": "function"}
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        export_to_csv(usage_graph, entity_metadata=entity_metadata, output_path=output_path)

        with open(output_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # Find module row
        module_row = next((r for r in rows if r['type'] == 'module'), None)
        assert module_row is not None
        assert module_row['name'] == 'module.py'
        assert module_row['parent_module'] == ''

        pathlib.Path(output_path).unlink()

    def test_export_entity_data(self):
        """Test that entity nodes are exported correctly."""
        usage_graph = {
            "/path/to/module.py": {
                "my_function": [],
                "MyClass": [],
            }
        }
        entity_metadata = {
            "/path/to/module.py": {
                "my_function": {"lines": 15, "entity_type": "function"},
                "MyClass": {"lines": 50, "entity_type": "class"},
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        export_to_csv(usage_graph, entity_metadata=entity_metadata, output_path=output_path)

        with open(output_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # Find function row
        func_row = next((r for r in rows if r['name'] == 'my_function'), None)
        assert func_row is not None
        assert func_row['type'] == 'function'
        assert func_row['parent_module'] == 'module.py'
        assert func_row['lines'] == '15'

        # Find class row
        class_row = next((r for r in rows if r['name'] == 'MyClass'), None)
        assert class_row is not None
        assert class_row['type'] == 'class'
        assert class_row['lines'] == '50'

        pathlib.Path(output_path).unlink()

    def test_export_links_count(self):
        """Test that links_in and links_out are calculated correctly."""
        usage_graph = {
            "/path/to/a.py": {
                "func_a": ["b.func_b", "b.func_c"],
            },
            "/path/to/b.py": {
                "func_b": [],
                "func_c": [],
            },
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        export_to_csv(usage_graph, output_path=output_path)

        with open(output_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # func_a should have links_out (dependencies)
        func_a_row = next((r for r in rows if r['name'] == 'func_a'), None)
        assert func_a_row is not None
        assert int(func_a_row['links_out']) >= 2

        # func_b should have links_in (being depended on)
        func_b_row = next((r for r in rows if r['name'] == 'func_b'), None)
        assert func_b_row is not None
        assert int(func_b_row['links_in']) >= 1

        pathlib.Path(output_path).unlink()

    def test_export_codegraph_on_itself(self):
        """Test CSV export on codegraph package itself."""
        codegraph_path = pathlib.Path(__file__).parents[1] / "codegraph"
        args = Namespace(paths=[codegraph_path.as_posix()])

        code_graph = CodeGraph(args)
        usage_graph = code_graph.usage_graph()
        entity_metadata = code_graph.get_entity_metadata()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name

        export_to_csv(usage_graph, entity_metadata=entity_metadata, output_path=output_path)

        with open(output_path, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

        # Should have modules
        module_names = [r['name'] for r in rows if r['type'] == 'module']
        assert 'core.py' in module_names
        assert 'parser.py' in module_names
        assert 'main.py' in module_names
        assert 'vizualyzer.py' in module_names

        # Should have functions and classes
        types = set(r['type'] for r in rows)
        assert 'module' in types
        assert 'function' in types
        assert 'class' in types

        # CodeGraph class should exist
        codegraph_row = next((r for r in rows if r['name'] == 'CodeGraph'), None)
        assert codegraph_row is not None
        assert codegraph_row['type'] == 'class'
        assert codegraph_row['parent_module'] == 'core.py'
        assert int(codegraph_row['lines']) > 0

        pathlib.Path(output_path).unlink()
