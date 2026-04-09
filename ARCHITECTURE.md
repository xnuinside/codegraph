# CodeGraph Architecture

This document describes the architecture and design of the CodeGraph tool.

## Overview

CodeGraph is a Python tool that creates dependency graphs from Python source code. It analyzes Python files, extracts function/class definitions and their relationships, and generates interactive visualizations.

## Project Structure

```
codegraph/
├── codegraph/              # Main package
│   ├── __init__.py         # Package init, version definition
│   ├── main.py             # CLI entry point (click-based)
│   ├── core.py             # Core graph building logic
│   ├── parser.py           # Python token parser (legacy, used by PythonParser)
│   ├── parsers/            # Pluggable language parsers
│   │   ├── base.py          # Parser interface
│   │   ├── python_parser.py # Python parser implementation
│   │   ├── rust_parser.py   # Rust parser stub
│   │   ├── registry.py      # Parser registry / discovery
│   ├── utils.py            # Utility functions
│   └── vizualyzer.py       # Visualization (D3.js + matplotlib)
├── tests/                  # Test suite
│   ├── test_codegraph.py   # Basic tests
│   ├── test_graph_generation.py  # Comprehensive graph tests
│   ├── test_utils.py       # Utility function tests
│   └── test_data/          # Test fixtures
├── docs/                   # Documentation
├── pyproject.toml          # Poetry configuration
├── tox.ini                 # Multi-version testing
└── .github/workflows/      # CI/CD
```

## Core Components

### 1. Parser Layer (`codegraph/parsers/`)

Parser implementations are pluggable via a registry. Each parser exposes:
- `get_source_files()` for language-specific file discovery
- `parse_files()` to produce module objects
- `usage_graph()` to build dependencies
- `get_entity_metadata()` for entity stats

This allows adding new languages without changing core graph orchestration.

#### Python Parser (`codegraph/parsers/python_parser.py`)

Uses Python's `ast` (and `typed_ast` for Python 2.x) to extract classes, functions,
imports, and line ranges.

#### Rust Parser (`codegraph/parsers/rust_parser.py`)

Currently a stub to establish extension points. The intent is to parse `.rs` files,
extract functions/structs/impl blocks, and build dependency edges using a Rust-aware parser.

**Key Classes:**
- `_Object` - Base class for all parsed objects (lineno, endno, name, parent)
- `Function` - Represents a function definition
- `AsyncFunction` - Represents an async function definition
- `Class` - Represents a class definition with methods
- `Import` - Collects all imports from a module

**Main Function:**
- `create_objects_array(fname, source)` - Parses source code and returns list of objects

**Import Handling:**
- Simple imports: `import os` → `['os']`
- From imports: `from os import path` → `['os.path']`
- Comma-separated: `from pkg import a, b, c` → `['pkg.a', 'pkg.b', 'pkg.c']`
- Aliased imports: `from pkg import mod as m` → `['pkg.mod as m']`

### 2. Core (`codegraph/core.py`)

The core module orchestrates parsing and visualization by delegating language-specific
work to the selected parser.

**Key Classes:**
- `CodeGraph` - Main class that orchestrates graph building

**Key Functions:**
- `usage_graph()` - Delegates to the active parser
- `get_entity_metadata()` - Delegates to the active parser

**Data Flow:**
```
Python Files → Parser → Code Objects → Import Analysis → Entity Usage → Dependency Graph
```

**Graph Format:**
```python
{
    "/path/to/module.py": {
        "function_name": ["other_module.func1", "local_func"],
        "class_name": ["dependency1"],
    }
}
```

### 3. Visualizer (`codegraph/vizualyzer.py`)

Provides two visualization modes: D3.js (default) and matplotlib (legacy).

**D3.js Visualization:**
- `convert_to_d3_format()` - Converts graph to D3.js node/link format
- `get_d3_html_template()` - Returns complete HTML with embedded D3.js
- `draw_graph()` - Saves HTML and opens in browser

**D3.js Features:**
- Force-directed layout for automatic node positioning
- Zoom/pan with mouse wheel and drag
- Node dragging to reposition
- Collapse/expand modules and entities
- Search with autocomplete
- Tooltips and statistics panel

**Matplotlib Visualization:**
- `draw_graph_matplotlib()` - Legacy visualization using networkx
- `process_module_in_graph()` - Process single module into graph

**D3.js Data Format:**
```json
{
  "nodes": [
    {"id": "module.py", "type": "module", "collapsed": false},
    {"id": "module.py:func", "label": "func", "type": "entity", "parent": "module.py"}
  ],
  "links": [
    {"source": "module.py", "target": "module.py:func", "type": "module-entity"},
    {"source": "module.py:func", "target": "other.py:dep", "type": "dependency"}
  ]
}
```

### 4. CLI (`codegraph/main.py`)

Click-based command-line interface.

**Options:**
- `paths` - Directory or file paths to analyze
- `--matplotlib` - Use legacy matplotlib visualization
- `--output` - Custom output path for HTML file

### 5. Utilities (`codegraph/utils.py`)

Helper functions for file system operations.

**Key Functions:**
- `get_python_paths_list(path)` - Recursively find all .py files

## Data Flow

```
1. CLI receives path(s)
        ↓
2. utils.get_python_paths_list() finds all .py files
        ↓
3. parser.create_objects_array() parses each file
   - Extracts functions, classes, methods
   - Collects import statements
        ↓
4. core.CodeGraph.usage_graph() builds dependency graph
   - Maps entities to line ranges
   - Finds entity usage in code
   - Creates dependency edges
        ↓
5. vizualyzer.draw_graph() creates visualization
   - Converts to D3.js format
   - Generates HTML with embedded JS
   - Opens in browser
```

## Node Types

| Type | Visual | Description |
|------|--------|-------------|
| Module | Green square | Python .py file |
| Entity | Blue circle | Function or class |
| External | Gray circle | Dependency from outside analyzed codebase |

## Link Types

| Type | Visual | Description |
|------|--------|-------------|
| module-entity | Green dashed | Module contains entity |
| module-module | Orange solid | Module imports from module |
| dependency | Red | Entity uses another entity |

## Testing Strategy

- **Unit tests**: Parser, import handling, utility functions
- **Integration tests**: Full graph generation on test data
- **Self-reference tests**: CodeGraph analyzing its own codebase
- **Multi-version**: Python 3.9 - 3.13 via tox

## Dependencies

- **networkx**: Graph data structure (for matplotlib mode)
- **matplotlib**: Legacy visualization
- **click**: CLI framework

## Extension Points

1. **New visualizers**: Add functions to `vizualyzer.py`
2. **New parsers**: Extend `parser.py` for other languages
3. **New link types**: Add to `convert_to_d3_format()`
4. **Export formats**: Add to `vizualyzer.py` (JSON, DOT, etc.)
