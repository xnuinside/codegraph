# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-17

### Added

**Interactive D3.js Visualization (New Default)**
- D3.js visualization is now the default instead of matplotlib
- Zoom & Pan: Mouse wheel to zoom, drag background to pan
- Drag nodes: Reposition individual nodes by dragging
- Collapse/Expand: Click on modules or entities to collapse/expand their children
- Double-click: Focus and zoom to any node
- Tooltips: Hover over nodes to see details (type, parent module, connection count)
- Auto zoom-to-fit: Graph automatically fits to screen after loading

**Module-to-Module Connections**
- Orange links now show dependencies between .py files
- Visual representation of which modules depend on which
- Module connections are always visible even when entities are collapsed

**Search with Autocomplete**
- Search box at the top center of the visualization
- Ctrl+F (Cmd+F on Mac) to focus search
- Autocomplete dropdown with up to 10 matching results
- Results show node type (module/entity/external) with color coding
- Arrow keys to navigate, Enter to select, Esc to close
- Highlighting: Selected node and its connections are highlighted, others dimmed
- Info panel shows number of connected nodes

**Visual Design**
- Modules: Green squares (larger)
- Entities: Blue circles (functions/classes)
- External dependencies: Gray circles
- Module-to-Module links: Orange, thick (3px)
- Module-to-Entity links: Green, dashed
- Entity-to-Dependency links: Red
- Statistics panel showing module count, entity count, and module connections
- Legend explaining all node and link types
- Dark theme with high contrast

**CLI Options**
- `--matplotlib` flag to use legacy matplotlib visualization
- `--output PATH` to specify custom output path for HTML file
- Default output: `./codegraph.html` (current working directory)

### Changed
- Default visualization changed from matplotlib to D3.js
- `draw_graph()` now generates interactive HTML instead of matplotlib window
- Renamed `draw_graph()` to `draw_graph_matplotlib()` for legacy visualization

### Fixed
- KeyError when analyzing codebases with external imports not in the analyzed path
- Now gracefully skips modules not found in the analyzed codebase
- Comma-separated imports now properly parsed (e.g., `from package import a, b, c`)
- Fixed missing connections when imports use comma-separated syntax

### Testing
- Added comprehensive test suite for graph generation (`tests/test_graph_generation.py`)
- Tests for import parsing: simple imports, comma-separated, aliased imports
- Tests for CodeGraph connections between modules
- Tests for D3.js format conversion
- Tests verifying codegraph can analyze its own codebase
- Support for Python 3.9, 3.10, 3.11, 3.12, 3.13
- Added `tox.ini` for multi-version testing
- Added GitHub Actions CI matrix for all supported Python versions

## [0.1.0] - Previous

### Added
- Initial matplotlib visualization
- Basic dependency graph generation
- CLI interface with click
- Support for Python 3.12+
