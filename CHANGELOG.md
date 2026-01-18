# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-01-18

### Added

**Enhanced Tooltips**
- Node tooltips now display "Links out" and "Links in" counts
- Color-coded: orange for outgoing links, green for incoming links
- Helps quickly understand node connectivity

**Links Count Panel**
- New "Links count" tab in the Unlinked Modules panel
- Configurable threshold filter (default: 1) to find nodes by connection count
- Checkboxes to filter by "links in" or "links out" criteria
- Click on any item to navigate and zoom to it on the graph
- Useful for finding highly connected or isolated nodes

**Display Filters**
- Show/hide nodes by type: Modules, Classes, Functions, External
- Show/hide links by type: Module→Module, Module→Entity, Dependencies
- All filters available in the expanded Display panel

**CSV Export**
- New `--csv PATH` option to export graph data to CSV file
- Columns: name, type (module/function/class/external), parent_module, full_path, links_out, links_in, lines
- Example: `codegraph /path/to/code --csv output.csv`

### Changed

- Legend panel moved to the right of Controls panel (both at top-left area)
- Renamed "Unlinked Modules" panel header, now uses tabs interface
- "Unlinked" is now a tab showing modules with zero connections
- "Links count" tab provides flexible filtering by connection count

### Refactored

**Template Extraction**
- HTML, CSS, and JavaScript moved to separate files in `codegraph/templates/`
- `templates/index.html` - HTML structure with placeholders
- `templates/styles.css` - all CSS styles
- `templates/main.js` - all JavaScript code
- `vizualyzer.py` reduced from ~2000 to ~340 lines
- Easier to maintain and edit frontend code separately

## [1.1.0] - 2025-01-18

### Added

**Massive Objects Detection**
- New "Massive Objects" panel to find large code entities by lines of code
- Filter by type: modules, classes, functions
- Configurable threshold (default: 50 lines)
- Click on any item to highlight it on the graph

**Lines of Code Tracking**
- Each entity (function, class, module) now tracks lines of code
- Lines of code displayed in tooltips
- Node size scales based on lines of code (toggleable in Display panel)

**Improved UI Panels**
- All panels are now draggable - move them anywhere on screen
- All panels are collapsible - click the toggle button to minimize
- Display panel with "Size by lines of code" toggle

**Smart Initial Zoom**
- Graph now auto-zooms based on node count
- Large graphs start more zoomed out for better overview

### Changed

**matplotlib is now optional**
- D3.js visualization works without matplotlib installed
- Install with `pip install codegraph[matplotlib]` for legacy matplotlib support
- Reduces installation size and dependencies for most users

### Testing
- Added package installation tests (`tests/test_package_install.py`)
- Tests verify package works without matplotlib
- Added CI jobs for package build and installation testing
- tox environments for testing with and without matplotlib

## [1.0.0] - 2025-01-18

### Added

**Live Demo & CI/CD**
- Interactive demo available at [xnuinside.github.io/codegraph](https://xnuinside.github.io/codegraph/)
- Automatic demo deployment on merge to main via GitHub Pages

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
- Multi-line imports with parentheses now properly parsed
- Fixed missing connections when imports use comma-separated or multi-line syntax
- Fixed missing module connections when imported names are variables (not functions/classes)

### Added
- **Class inheritance detection**: Classes now show connections to their base classes
- Supports single and multiple inheritance: `class Child(Base1, Base2)`
- Supports multi-line inheritance declarations
- **`__init__.py` support**: Now includes `__init__.py` files in analysis
- Re-export connections from `__init__.py` are shown as dependencies
- **Unlinked Modules Panel**: Shows list of modules with no connections (neither incoming nor outgoing)
- Click on module name to navigate and zoom to it on the graph
- **Full Path in Tooltip**: Hovering over modules now shows relative path (e.g., "Full Path: tests/test_comments.py")

### Changed
- Replaced print statements with logging/click.echo for proper CLI output
- Module-to-module links now created based on imports, not just entity usage (connections shown even when importing variables or constants)

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
