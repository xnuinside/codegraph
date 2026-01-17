### CodeGraph - static code analyzator, that create a diagram with your code structure.

![badge1](https://img.shields.io/pypi/v/codegraph) ![badge2](https://img.shields.io/pypi/l/codegraph) ![badge3](https://img.shields.io/pypi/pyversions/codegraph)![workflow](https://github.com/xnuinside/codegraph/actions/workflows/main.yml/badge.svg)

**[Live Demo](https://xnuinside.github.io/codegraph/)** - Interactive visualization of [simple-ddl-parser](https://github.com/xnuinside/simple-ddl-parser) codebase

Tool that creates a diagram with your code structure to show dependencies between code entities (methods, modules, classes and etc).
Main advantage of CodeGraph is that it does not execute the code itself. You don't need to activate any environments or install dependencies to analyze the target code.
It is based only on lexical and syntax parsing, so it doesn't need to install all your code dependencies.

### Interactive Visualization

![Interactive Code Visualization](docs/img/interactive_code_visualization.png)

**Zoom, Pan & Drag** - Use mouse wheel to zoom, drag background to pan, drag nodes to reposition them.

### Search & Highlight

![Node Search](docs/img/node_search.png)

**Search with Autocomplete** - Press `Ctrl+F` (or `Cmd+F` on Mac) to search. Results show node type with color coding.

![Highlight Nodes](docs/img/highlight_nodes.png)

**Highlight Connections** - Click on any node to highlight it and all connected nodes. Others will be dimmed.

### Node Information

![Node Information](docs/img/node_information.png)

**Tooltips** - Hover over any node to see details: type, parent module, full path, and connection count.

### Unlinked Modules

![Unlinked Nodes](docs/img/listing_unlinked_nodes.png)

**Unlinked Panel** - Shows modules with no connections. Click to navigate to them on the graph.

### UI Tips

![UI Tips](docs/img/tips_in_ui.png)

**Built-in Help** - Legend and keyboard shortcuts are always visible in the UI.

---

### Installation

```console
pip install codegraph
```

### Usage

```console
codegraph /path/to/your_python_code
```

This will generate an interactive HTML visualization and open it in your browser.

### CLI Options

| Option | Description |
|--------|-------------|
| `--output PATH` | Custom output path for HTML file (default: `./codegraph.html`) |
| `--matplotlib` | Use legacy matplotlib visualization instead of D3.js |
| `-o, --object-only` | Print dependencies to console only, no visualization |

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.
