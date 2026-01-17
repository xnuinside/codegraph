import json
import logging
import os
import webbrowser
from typing import Dict, List

import matplotlib.pyplot as plt
import networkx as nx

logger = logging.getLogger(__name__)


def process_module_in_graph(module: Dict[str, list], module_links: list, G: nx.DiGraph):
    _module = os.path.basename(module)

    module_edges = []

    sub_edges = []
    for entity in module_links:
        module_edges.append((_module, entity))
        for dep in module_links[entity]:
            if "." in dep:
                dep = dep.split(".")[1].replace(".", ".py")
            sub_edges.append((entity, dep))
        G.add_edges_from(sub_edges)
    if not module_links:
        G.add_node(_module)
    G.add_edges_from(module_edges)
    return module_edges, sub_edges


def draw_graph_matplotlib(modules_entities: Dict) -> None:

    G = nx.DiGraph()

    module_edges_all = []

    sub_edges_all = []

    for module in modules_entities:
        new_module_edges_all, new_edges_all = process_module_in_graph(
            module, modules_entities[module], G
        )

        module_edges_all += new_module_edges_all
        sub_edges_all += new_edges_all

    pos = nx.spring_layout(G)
    module_list = [os.path.basename(module) for module in modules_entities]
    module_list_labels = {module_name: module_name for module_name in module_list}

    entities_labels = {edge[1]: edge[1] for edge in module_edges_all}
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=module_list,
        node_color="#009c2c",
        node_size=800,
        node_shape="s",
        alpha=0.8,
    )
    nx.draw(
        G,
        pos,
        node_color="#009c2c",
        arrows=False,
        edge_color="#ffffff",
        node_shape="o",
        alpha=0.8,
    )

    nx.draw_networkx_labels(
        G, pos, labels=module_list_labels, font_weight="bold", font_size=11
    )
    nx.draw_networkx_labels(
        G,
        pos,
        labels=entities_labels,
        font_weight="bold",
        font_family="Arial",
        font_size=10,
    )

    arrow_size = 15

    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=module_edges_all,
        edge_color="#009c2c",
        width=2,
        arrows=True,
        arrowsize=arrow_size,
        style="dashed",
        node_size=50,
    )
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=sub_edges_all,
        edge_color="r",
        width=2,
        arrows=True,
        arrowsize=arrow_size,
        style="dashed",
    )
    for p in pos:
        pos[p][1] += 0.07
    plt.show()


def convert_to_d3_format(modules_entities: Dict) -> Dict:
    """Convert the modules_entities graph data to D3.js format."""
    nodes: List[Dict] = []
    links: List[Dict] = []
    node_ids = set()
    module_links = set()  # Track module-to-module links
    module_full_paths: Dict[str, str] = {}  # Map module name to full path

    # Find common root path for relative paths
    all_paths = list(modules_entities.keys())
    if all_paths:
        common_prefix = os.path.commonpath(all_paths)
        # Go up one level to include the root folder name
        common_root = os.path.dirname(common_prefix)
    else:
        common_root = ""

    # First pass: build entity-to-module mapping and create ALL nodes
    entity_to_module: Dict[str, str] = {}
    for module_path, entities in modules_entities.items():
        module_name = os.path.basename(module_path)

        # Compute relative path from common root
        if common_root:
            relative_path = os.path.relpath(module_path, common_root)
        else:
            relative_path = module_path

        module_full_paths[module_name] = relative_path

        # Add module node
        if module_name not in node_ids:
            nodes.append({
                "id": module_name,
                "type": "module",
                "collapsed": False,
                "fullPath": relative_path
            })
            node_ids.add(module_name)

        # Add entity nodes and build mapping
        for entity_name in entities.keys():
            entity_id = f"{module_name}:{entity_name}"
            entity_to_module[entity_name] = module_name
            entity_to_module[f"{module_name.replace('.py', '')}.{entity_name}"] = module_name

            if entity_id not in node_ids:
                nodes.append({
                    "id": entity_id,
                    "label": entity_name,
                    "type": "entity",
                    "parent": module_name
                })
                node_ids.add(entity_id)

    # Second pass: create all links
    for module_path, entities in modules_entities.items():
        module_name = os.path.basename(module_path)

        for entity_name, dependencies in entities.items():
            entity_id = f"{module_name}:{entity_name}"

            # Link from module to entity
            links.append({
                "source": module_name,
                "target": entity_id,
                "type": "module-entity"
            })

            # Links from entity to dependencies
            for dep in dependencies:
                # Parse dependency name
                dep_module = None
                dep_entity = dep

                if "." in dep:
                    parts = dep.split(".")
                    dep_module_name = parts[0]
                    dep_entity = parts[1] if len(parts) > 1 else parts[0]
                    # Find the actual module from mapping
                    if dep in entity_to_module:
                        dep_module = entity_to_module[dep]
                    elif f"{dep_module_name}.py" in node_ids:
                        dep_module = f"{dep_module_name}.py"

                # Special case: module._ means importing from a module (re-export)
                # This creates a module-to-module link
                if dep_entity == "_" and dep_module:
                    link_key = (module_name, dep_module)
                    if link_key not in module_links:
                        module_links.add(link_key)
                    continue  # Don't create entity-level link for module imports

                # Try to resolve dependency to existing entity
                dep_target = None
                for m_path, m_entities in modules_entities.items():
                    m_name = os.path.basename(m_path)
                    if dep_entity in m_entities:
                        dep_target = f"{m_name}:{dep_entity}"
                        dep_module = m_name
                        break

                if dep_target and dep_target in node_ids:
                    # Link to existing entity
                    links.append({
                        "source": entity_id,
                        "target": dep_target,
                        "type": "dependency"
                    })
                    # Add module-to-module link if different modules
                    if dep_module and dep_module != module_name:
                        link_key = (module_name, dep_module)
                        if link_key not in module_links:
                            module_links.add(link_key)
                else:
                    # Add as external dependency node
                    if dep_entity not in node_ids:
                        nodes.append({
                            "id": dep_entity,
                            "type": "external",
                            "label": dep_entity
                        })
                        node_ids.add(dep_entity)

                    links.append({
                        "source": entity_id,
                        "target": dep_entity,
                        "type": "dependency"
                    })

    # Add module-to-module links
    for source_module, target_module in module_links:
        links.append({
            "source": source_module,
            "target": target_module,
            "type": "module-module"
        })

    # Find unlinked modules (no connections at all - neither incoming nor outgoing)
    all_modules = {n["id"] for n in nodes if n["type"] == "module"}
    # Modules that import something (outgoing)
    modules_with_outgoing = {source for source, target in module_links}
    # Modules that are imported (incoming)
    modules_with_incoming = {target for source, target in module_links}
    # Modules with any connection
    linked_modules = modules_with_outgoing | modules_with_incoming
    unlinked_modules = [
        {"id": m, "fullPath": module_full_paths.get(m, m)}
        for m in sorted(all_modules - linked_modules)
    ]

    return {"nodes": nodes, "links": links, "unlinkedModules": unlinked_modules}


def get_d3_html_template(graph_data: Dict) -> str:
    """Generate HTML with embedded D3.js visualization."""
    graph_json = json.dumps(graph_data, indent=2)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeGraph - Interactive Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            overflow: hidden;
        }}
        #graph {{
            width: 100vw;
            height: 100vh;
        }}
        .node {{
            cursor: pointer;
        }}
        .node-module {{
            fill: #009c2c;
            stroke: #00ff44;
            stroke-width: 2px;
        }}
        .node-module.collapsed {{
            fill: #006618;
            stroke: #00ff44;
            stroke-width: 3px;
            stroke-dasharray: 4, 2;
        }}
        .node-entity {{
            fill: #4a90d9;
            stroke: #70b8ff;
            stroke-width: 1.5px;
        }}
        .node-entity.collapsed {{
            fill: #2a5080;
            stroke: #70b8ff;
            stroke-width: 2px;
            stroke-dasharray: 3, 2;
        }}
        .node-external {{
            fill: #808080;
            stroke: #aaaaaa;
            stroke-width: 1px;
        }}
        .node:hover {{
            filter: brightness(1.3);
        }}
        .node-hidden {{
            opacity: 0;
            pointer-events: none;
        }}
        .link {{
            fill: none;
            stroke-opacity: 0.6;
        }}
        .link-module-module {{
            stroke: #ff9800;
            stroke-width: 3px;
            stroke-opacity: 0.8;
        }}
        .link-module-entity {{
            stroke: #009c2c;
            stroke-width: 1.5px;
            stroke-dasharray: 5, 3;
        }}
        .link-dependency {{
            stroke: #d94a4a;
            stroke-width: 1.5px;
        }}
        .link-hidden {{
            opacity: 0;
        }}
        .label {{
            font-size: 11px;
            fill: #ffffff;
            pointer-events: none;
            text-shadow: 0 0 3px #000, 0 0 6px #000;
        }}
        .label-module {{
            font-size: 13px;
            font-weight: bold;
        }}
        .label-hidden {{
            opacity: 0;
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.9);
            color: #fff;
            padding: 10px 14px;
            border-radius: 6px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            border: 1px solid #555;
            max-width: 300px;
        }}
        .controls {{
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            color: #fff;
            font-size: 12px;
            z-index: 1000;
        }}
        .controls h3 {{
            margin-bottom: 10px;
            color: #70b8ff;
        }}
        .controls p {{
            margin: 5px 0;
            color: #ccc;
        }}
        .controls kbd {{
            background: #333;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
        }}
        .legend {{
            position: fixed;
            bottom: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            color: #fff;
            font-size: 12px;
        }}
        .legend h4 {{
            margin-bottom: 8px;
            color: #70b8ff;
        }}
        .legend-section {{
            margin-bottom: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 4px 0;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 3px;
        }}
        .legend-line {{
            width: 30px;
            height: 3px;
            margin-right: 10px;
        }}
        .legend-module {{ background: #009c2c; }}
        .legend-entity {{ background: #4a90d9; border-radius: 50%; }}
        .legend-external {{ background: #808080; border-radius: 50%; }}
        .legend-link-module {{ background: #ff9800; }}
        .legend-link-entity {{ background: #009c2c; }}
        .legend-link-dep {{ background: #d94a4a; }}
        .stats {{
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            color: #fff;
            font-size: 12px;
        }}
        .stats h4 {{
            margin-bottom: 8px;
            color: #70b8ff;
        }}
        .unlinked-modules {{
            position: fixed;
            top: 130px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 8px;
            color: #fff;
            font-size: 12px;
            max-height: 300px;
            max-width: 280px;
            overflow-y: auto;
        }}
        .unlinked-modules h4 {{
            margin-bottom: 8px;
            color: #ff9800;
        }}
        .unlinked-modules .count {{
            color: #888;
            font-size: 11px;
            margin-left: 5px;
        }}
        .unlinked-modules ul {{
            list-style: none;
            margin: 0;
            padding: 0;
        }}
        .unlinked-modules li {{
            padding: 4px 8px;
            margin: 2px 0;
            cursor: pointer;
            border-radius: 4px;
            transition: background 0.2s;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .unlinked-modules li:hover {{
            background: rgba(255, 152, 0, 0.3);
        }}
        .unlinked-modules li .path {{
            color: #888;
            font-size: 10px;
            display: block;
            margin-top: 2px;
        }}
        .unlinked-modules::-webkit-scrollbar {{
            width: 6px;
        }}
        .unlinked-modules::-webkit-scrollbar-thumb {{
            background: #555;
            border-radius: 3px;
        }}
        /* Search box styles */
        .search-container {{
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 1001;
            width: 350px;
        }}
        .search-box {{
            position: relative;
            width: 100%;
        }}
        .search-input {{
            width: 100%;
            padding: 12px 40px 12px 16px;
            font-size: 14px;
            border: 2px solid #444;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.9);
            color: #fff;
            outline: none;
            transition: border-color 0.2s, box-shadow 0.2s;
        }}
        .search-input:focus {{
            border-color: #70b8ff;
            box-shadow: 0 0 10px rgba(112, 184, 255, 0.3);
        }}
        .search-input::placeholder {{
            color: #888;
        }}
        .search-clear {{
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            color: #888;
            font-size: 18px;
            cursor: pointer;
            padding: 4px;
            display: none;
        }}
        .search-clear:hover {{
            color: #fff;
        }}
        .search-clear.visible {{
            display: block;
        }}
        .autocomplete-list {{
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            max-height: 300px;
            overflow-y: auto;
            background: rgba(0, 0, 0, 0.95);
            border: 1px solid #444;
            border-top: none;
            border-radius: 0 0 8px 8px;
            display: none;
        }}
        .autocomplete-list.visible {{
            display: block;
        }}
        .autocomplete-item {{
            padding: 10px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            border-bottom: 1px solid #333;
        }}
        .autocomplete-item:last-child {{
            border-bottom: none;
        }}
        .autocomplete-item:hover,
        .autocomplete-item.selected {{
            background: rgba(112, 184, 255, 0.2);
        }}
        .autocomplete-item .node-type {{
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 3px;
            text-transform: uppercase;
            font-weight: bold;
        }}
        .autocomplete-item .node-type.module {{
            background: #009c2c;
            color: #fff;
        }}
        .autocomplete-item .node-type.entity {{
            background: #4a90d9;
            color: #fff;
        }}
        .autocomplete-item .node-type.external {{
            background: #808080;
            color: #fff;
        }}
        .autocomplete-item .node-name {{
            color: #fff;
            flex: 1;
        }}
        .autocomplete-item .node-parent {{
            color: #888;
            font-size: 12px;
        }}
        .highlight-info {{
            position: fixed;
            bottom: 10px;
            right: 10px;
            background: rgba(112, 184, 255, 0.9);
            color: #000;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 12px;
            display: none;
            align-items: center;
            gap: 10px;
        }}
        .highlight-info.visible {{
            display: flex;
        }}
        .highlight-info button {{
            background: #333;
            color: #fff;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .highlight-info button:hover {{
            background: #555;
        }}
        /* Dimmed state for non-highlighted nodes/links */
        .node.dimmed {{
            opacity: 0.15;
        }}
        .link.dimmed {{
            opacity: 0.05;
        }}
        .label.dimmed {{
            opacity: 0.1;
        }}
        /* Highlighted state */
        .node.highlighted {{
            filter: brightness(1.3) drop-shadow(0 0 8px rgba(255, 255, 255, 0.5));
        }}
        .node.highlighted-main {{
            filter: brightness(1.5) drop-shadow(0 0 15px rgba(112, 184, 255, 0.8));
        }}
        .link.highlighted {{
            stroke-opacity: 1;
            filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.5));
        }}
    </style>
</head>
<body>
    <div id="graph"></div>
    <div class="tooltip" id="tooltip"></div>

    <!-- Search box -->
    <div class="search-container">
        <div class="search-box">
            <input type="text" class="search-input" id="searchInput" placeholder="Search nodes... (Ctrl+F)" autocomplete="off">
            <button class="search-clear" id="searchClear">&times;</button>
            <div class="autocomplete-list" id="autocompleteList"></div>
        </div>
    </div>

    <!-- Highlight info banner -->
    <div class="highlight-info" id="highlightInfo">
        <span id="highlightText">Highlighting: </span>
        <button id="clearHighlight">Clear (Esc)</button>
    </div>

    <div class="controls">
        <h3>Controls</h3>
        <p><kbd>Ctrl+F</kbd> Search nodes</p>
        <p><kbd>Scroll</kbd> Zoom in/out</p>
        <p><kbd>Drag</kbd> on background - Pan</p>
        <p><kbd>Drag</kbd> on node - Move node</p>
        <p><kbd>Click</kbd> module/entity - Collapse/Expand</p>
        <p><kbd>Double-click</kbd> - Focus on node</p>
        <p><kbd>Esc</kbd> Clear search highlight</p>
    </div>
    <div class="legend">
        <div class="legend-section">
            <h4>Nodes</h4>
            <div class="legend-item">
                <div class="legend-color legend-module"></div>
                <span>Module (.py file)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color legend-entity"></div>
                <span>Entity (function/class)</span>
            </div>
            <div class="legend-item">
                <div class="legend-color legend-external"></div>
                <span>External dependency</span>
            </div>
        </div>
        <div class="legend-section">
            <h4>Links</h4>
            <div class="legend-item">
                <div class="legend-line legend-link-module"></div>
                <span>Module → Module</span>
            </div>
            <div class="legend-item">
                <div class="legend-line legend-link-entity" style="border-top: 2px dashed #009c2c; background: none; height: 0;"></div>
                <span>Module → Entity</span>
            </div>
            <div class="legend-item">
                <div class="legend-line legend-link-dep"></div>
                <span>Entity → Dependency</span>
            </div>
        </div>
    </div>
    <div class="stats" id="stats"></div>
    <div class="unlinked-modules" id="unlinked-modules"></div>

    <script>
        const graphData = {graph_json};

        // Calculate stats
        const moduleCount = graphData.nodes.filter(n => n.type === 'module').length;
        const entityCount = graphData.nodes.filter(n => n.type === 'entity').length;
        const moduleLinks = graphData.links.filter(l => l.type === 'module-module').length;
        document.getElementById('stats').innerHTML = `
            <h4>Statistics</h4>
            <p>Modules: ${{moduleCount}}</p>
            <p>Entities: ${{entityCount}}</p>
            <p>Module connections: ${{moduleLinks}}</p>
        `;

        // Populate unlinked modules panel
        const unlinkedModules = graphData.unlinkedModules || [];
        const unlinkedPanel = document.getElementById('unlinked-modules');
        if (unlinkedModules.length > 0) {{
            unlinkedPanel.innerHTML = `
                <h4>Unlinked <span class="count">(${{unlinkedModules.length}})</span></h4>
                <ul>
                    ${{unlinkedModules.map(m => `
                        <li data-module-id="${{m.id}}" title="${{m.fullPath}}">
                            ${{m.id}}
                            <span class="path">${{m.fullPath}}</span>
                        </li>
                    `).join('')}}
                </ul>
            `;
        }} else {{
            unlinkedPanel.style.display = 'none';
        }}

        const width = window.innerWidth;
        const height = window.innerHeight;

        // Create SVG
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        // Add zoom behavior
        const g = svg.append("g");

        const zoom = d3.zoom()
            .scaleExtent([0.05, 4])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});

        svg.call(zoom);

        // Tooltip
        const tooltip = d3.select("#tooltip");

        // Track collapsed nodes (modules and entities)
        const collapsedNodes = new Set();

        // Create arrow markers for different link types
        const defs = svg.append("defs");

        // Module-module arrow (orange)
        defs.append("marker")
            .attr("id", "arrow-module-module")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 25)
            .attr("refY", 0)
            .attr("markerWidth", 8)
            .attr("markerHeight", 8)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", "#ff9800")
            .attr("d", "M0,-5L10,0L0,5");

        // Module-entity arrow (green)
        defs.append("marker")
            .attr("id", "arrow-module-entity")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 18)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", "#009c2c")
            .attr("d", "M0,-5L10,0L0,5");

        // Dependency arrow (red)
        defs.append("marker")
            .attr("id", "arrow-dependency")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 18)
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("fill", "#d94a4a")
            .attr("d", "M0,-5L10,0L0,5");

        // Create force simulation with adjusted parameters
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links).id(d => d.id).distance(d => {{
                if (d.type === 'module-module') return 200;
                if (d.type === 'module-entity') return 60;
                return 80;
            }}))
            .force("charge", d3.forceManyBody().strength(d => {{
                if (d.type === 'module') return -500;
                return -150;
            }}))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(d => {{
                if (d.type === 'module') return 50;
                return 25;
            }}));

        // Create links (module-module first so they appear behind)
        const link = g.append("g")
            .selectAll("line")
            .data(graphData.links.sort((a, b) => {{
                const order = {{'module-module': 0, 'module-entity': 1, 'dependency': 2}};
                return (order[a.type] || 2) - (order[b.type] || 2);
            }}))
            .join("line")
            .attr("class", d => `link link-${{d.type}}`)
            .attr("marker-end", d => `url(#arrow-${{d.type}})`);

        // Create nodes
        const node = g.append("g")
            .selectAll("g")
            .data(graphData.nodes)
            .join("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Add shapes based on node type
        node.each(function(d) {{
            const el = d3.select(this);
            if (d.type === "module") {{
                el.append("rect")
                    .attr("class", "node-module")
                    .attr("width", 30)
                    .attr("height", 30)
                    .attr("x", -15)
                    .attr("y", -15)
                    .attr("rx", 4);
            }} else if (d.type === "entity") {{
                el.append("circle")
                    .attr("class", "node-entity")
                    .attr("r", 10);
            }} else {{
                el.append("circle")
                    .attr("class", "node-external")
                    .attr("r", 7);
            }}
        }});

        // Add labels
        const labels = g.append("g")
            .selectAll("text")
            .data(graphData.nodes)
            .join("text")
            .attr("class", d => `label ${{d.type === 'module' ? 'label-module' : ''}}`)
            .attr("dy", d => d.type === "module" ? 30 : 20)
            .attr("text-anchor", "middle")
            .text(d => d.label || d.id);

        // Node interactions
        node.on("mouseover", function(event, d) {{
            // Highlight connected links
            link.style("stroke-opacity", l => {{
                const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                return (sourceId === d.id || targetId === d.id) ? 1 : 0.2;
            }});

            // Count connections
            const outgoing = graphData.links.filter(l => {{
                const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                return sourceId === d.id;
            }}).length;
            const incoming = graphData.links.filter(l => {{
                const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                return targetId === d.id;
            }}).length;

            tooltip
                .style("opacity", 1)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px")
                .html(`
                    <strong>${{d.label || d.id}}</strong><br>
                    Type: ${{d.type}}<br>
                    ${{d.fullPath ? 'Full Path: ' + d.fullPath + '<br>' : ''}}
                    ${{d.parent ? 'Module: ' + d.parent + '<br>' : ''}}
                    Outgoing: ${{outgoing}} | Incoming: ${{incoming}}
                    ${{collapsedNodes.has(d.id) ? '<br><em>(collapsed)</em>' : ''}}
                `);
        }})
        .on("mouseout", function() {{
            link.style("stroke-opacity", 0.6);
            tooltip.style("opacity", 0);
        }})
        .on("click", function(event, d) {{
            if (d.type === "module" || d.type === "entity") {{
                toggleCollapse(d);
            }}
        }})
        .on("dblclick", function(event, d) {{
            // Focus on this node (zoom to it)
            event.stopPropagation();
            const scale = 1.5;
            svg.transition()
                .duration(500)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(width / 2, height / 2)
                    .scale(scale)
                    .translate(-d.x, -d.y));
        }});

        function toggleCollapse(targetNode) {{
            const nodeId = targetNode.id;

            if (collapsedNodes.has(nodeId)) {{
                collapsedNodes.delete(nodeId);
            }} else {{
                collapsedNodes.add(nodeId);
            }}

            // Update node visual to show collapsed state
            node.select("rect, circle")
                .classed("collapsed", d => collapsedNodes.has(d.id));

            updateVisibility();
        }}

        function getChildNodes(nodeId, nodeType) {{
            // Get all nodes that are direct children of this node
            const children = new Set();

            if (nodeType === 'module') {{
                // Module's children are entities with this module as parent
                graphData.nodes.forEach(n => {{
                    if (n.parent === nodeId) {{
                        children.add(n.id);
                    }}
                }});
            }} else if (nodeType === 'entity') {{
                // Entity's children are nodes it links to via dependency
                graphData.links.forEach(l => {{
                    const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                    const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                    if (sourceId === nodeId && l.type === 'dependency') {{
                        children.add(targetId);
                    }}
                }});
            }}

            return children;
        }}

        function isNodeHidden(nodeData) {{
            // Module nodes are never hidden
            if (nodeData.type === 'module') return false;

            // Check if parent module is collapsed
            if (nodeData.parent && collapsedNodes.has(nodeData.parent)) {{
                return true;
            }}

            // Check if this is a dependency of a collapsed entity
            for (const link of graphData.links) {{
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;

                if (targetId === nodeData.id && link.type === 'dependency') {{
                    // Check if source entity is collapsed or hidden
                    const sourceNode = graphData.nodes.find(n => n.id === sourceId);
                    if (sourceNode) {{
                        if (collapsedNodes.has(sourceId)) return true;
                        if (sourceNode.parent && collapsedNodes.has(sourceNode.parent)) return true;
                    }}
                }}
            }}

            return false;
        }}

        function updateVisibility() {{
            // Update node visibility
            node.classed("node-hidden", d => isNodeHidden(d));

            // Update label visibility
            labels.classed("label-hidden", d => isNodeHidden(d));

            // Update link visibility
            link.classed("link-hidden", d => {{
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;

                // Module-module links are only hidden if connecting collapsed modules in certain ways
                if (d.type === 'module-module') {{
                    return false; // Always show module-module links
                }}

                const sourceNode = graphData.nodes.find(n => n.id === sourceId);
                const targetNode = graphData.nodes.find(n => n.id === targetId);

                if (sourceNode && isNodeHidden(sourceNode)) return true;
                if (targetNode && isNodeHidden(targetNode)) return true;

                // Hide module-entity links if module is collapsed
                if (d.type === 'module-entity' && collapsedNodes.has(sourceId)) {{
                    return true;
                }}

                // Hide dependency links if source entity is collapsed
                if (d.type === 'dependency' && collapsedNodes.has(sourceId)) {{
                    return true;
                }}

                return false;
            }});
        }}

        // Simulation tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);

            labels
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});

        // Drag functions
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        // Initial zoom to fit content
        simulation.on("end", () => {{
            // Calculate bounds
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            graphData.nodes.forEach(n => {{
                minX = Math.min(minX, n.x);
                maxX = Math.max(maxX, n.x);
                minY = Math.min(minY, n.y);
                maxY = Math.max(maxY, n.y);
            }});

            const padding = 50;
            const graphWidth = maxX - minX + padding * 2;
            const graphHeight = maxY - minY + padding * 2;
            const scale = Math.min(width / graphWidth, height / graphHeight, 1) * 0.9;
            const centerX = (minX + maxX) / 2;
            const centerY = (minY + maxY) / 2;

            svg.transition()
                .duration(500)
                .call(zoom.transform, d3.zoomIdentity
                    .translate(width / 2, height / 2)
                    .scale(scale)
                    .translate(-centerX, -centerY));
        }});

        // ==================== SEARCH FUNCTIONALITY ====================

        const searchInput = document.getElementById('searchInput');
        const searchClear = document.getElementById('searchClear');
        const autocompleteList = document.getElementById('autocompleteList');
        const highlightInfo = document.getElementById('highlightInfo');
        const highlightText = document.getElementById('highlightText');
        const clearHighlightBtn = document.getElementById('clearHighlight');

        let selectedAutocompleteIndex = -1;
        let currentHighlightedNode = null;
        let filteredNodes = [];

        // Build searchable index
        const searchIndex = graphData.nodes.map(n => ({{
            id: n.id,
            label: n.label || n.id,
            type: n.type,
            parent: n.parent || null,
            searchText: ((n.label || n.id) + ' ' + (n.parent || '')).toLowerCase()
        }}));

        // Get connected nodes for a given node
        function getConnectedNodes(nodeId) {{
            const connected = new Set();
            connected.add(nodeId);

            graphData.links.forEach(l => {{
                const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                const targetId = typeof l.target === 'object' ? l.target.id : l.target;

                if (sourceId === nodeId) {{
                    connected.add(targetId);
                }}
                if (targetId === nodeId) {{
                    connected.add(sourceId);
                }}
            }});

            return connected;
        }}

        // Get connected links for a given node
        function getConnectedLinks(nodeId) {{
            return graphData.links.filter(l => {{
                const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
                const targetId = typeof l.target === 'object' ? l.target.id : l.target;
                return sourceId === nodeId || targetId === nodeId;
            }});
        }}

        // Highlight a node and its connections
        function highlightNode(nodeId) {{
            const connectedNodes = getConnectedNodes(nodeId);
            currentHighlightedNode = nodeId;

            // Update nodes
            node.classed('dimmed', d => !connectedNodes.has(d.id))
                .classed('highlighted', d => connectedNodes.has(d.id) && d.id !== nodeId)
                .classed('highlighted-main', d => d.id === nodeId);

            // Update links
            link.classed('dimmed', d => {{
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                return sourceId !== nodeId && targetId !== nodeId;
            }})
            .classed('highlighted', d => {{
                const sourceId = typeof d.source === 'object' ? d.source.id : d.source;
                const targetId = typeof d.target === 'object' ? d.target.id : d.target;
                return sourceId === nodeId || targetId === nodeId;
            }});

            // Update labels
            labels.classed('dimmed', d => !connectedNodes.has(d.id));

            // Show highlight info
            const nodeData = graphData.nodes.find(n => n.id === nodeId);
            highlightText.textContent = `Highlighting: ${{nodeData.label || nodeData.id}} (${{connectedNodes.size}} connected)`;
            highlightInfo.classList.add('visible');

            // Zoom to the node
            const targetNode = graphData.nodes.find(n => n.id === nodeId);
            if (targetNode) {{
                const scale = 1.2;
                svg.transition()
                    .duration(500)
                    .call(zoom.transform, d3.zoomIdentity
                        .translate(width / 2, height / 2)
                        .scale(scale)
                        .translate(-targetNode.x, -targetNode.y));
            }}
        }}

        // Clear all highlighting
        function clearHighlight() {{
            currentHighlightedNode = null;

            node.classed('dimmed', false)
                .classed('highlighted', false)
                .classed('highlighted-main', false);

            link.classed('dimmed', false)
                .classed('highlighted', false);

            labels.classed('dimmed', false);

            highlightInfo.classList.remove('visible');
            searchInput.value = '';
            searchClear.classList.remove('visible');
            hideAutocomplete();
        }}

        // Filter nodes based on search query
        function filterNodes(query) {{
            if (!query) return [];
            const lowerQuery = query.toLowerCase();
            return searchIndex
                .filter(n => n.searchText.includes(lowerQuery))
                .slice(0, 10); // Limit to 10 results
        }}

        // Render autocomplete list
        function renderAutocomplete(results) {{
            if (results.length === 0) {{
                hideAutocomplete();
                return;
            }}

            filteredNodes = results;
            selectedAutocompleteIndex = -1;

            autocompleteList.innerHTML = results.map((n, i) => `
                <div class="autocomplete-item" data-index="${{i}}" data-id="${{n.id}}">
                    <span class="node-type ${{n.type}}">${{n.type}}</span>
                    <span class="node-name">${{n.label}}</span>
                    ${{n.parent ? `<span class="node-parent">${{n.parent}}</span>` : ''}}
                </div>
            `).join('');

            autocompleteList.classList.add('visible');

            // Add click handlers
            autocompleteList.querySelectorAll('.autocomplete-item').forEach(item => {{
                item.addEventListener('click', () => {{
                    selectNode(item.dataset.id);
                }});
            }});
        }}

        // Hide autocomplete
        function hideAutocomplete() {{
            autocompleteList.classList.remove('visible');
            filteredNodes = [];
            selectedAutocompleteIndex = -1;
        }}

        // Select a node from autocomplete
        function selectNode(nodeId) {{
            const nodeData = searchIndex.find(n => n.id === nodeId);
            if (nodeData) {{
                searchInput.value = nodeData.label;
                hideAutocomplete();
                highlightNode(nodeId);
            }}
        }}

        // Update selected item in autocomplete
        function updateSelectedItem() {{
            const items = autocompleteList.querySelectorAll('.autocomplete-item');
            items.forEach((item, i) => {{
                item.classList.toggle('selected', i === selectedAutocompleteIndex);
            }});

            // Scroll into view
            if (selectedAutocompleteIndex >= 0 && items[selectedAutocompleteIndex]) {{
                items[selectedAutocompleteIndex].scrollIntoView({{ block: 'nearest' }});
            }}
        }}

        // Search input event handlers
        searchInput.addEventListener('input', (e) => {{
            const query = e.target.value.trim();
            searchClear.classList.toggle('visible', query.length > 0);

            if (query.length > 0) {{
                const results = filterNodes(query);
                renderAutocomplete(results);
            }} else {{
                hideAutocomplete();
            }}
        }});

        searchInput.addEventListener('keydown', (e) => {{
            if (e.key === 'ArrowDown') {{
                e.preventDefault();
                if (filteredNodes.length > 0) {{
                    selectedAutocompleteIndex = Math.min(selectedAutocompleteIndex + 1, filteredNodes.length - 1);
                    updateSelectedItem();
                }}
            }} else if (e.key === 'ArrowUp') {{
                e.preventDefault();
                if (filteredNodes.length > 0) {{
                    selectedAutocompleteIndex = Math.max(selectedAutocompleteIndex - 1, 0);
                    updateSelectedItem();
                }}
            }} else if (e.key === 'Enter') {{
                e.preventDefault();
                if (selectedAutocompleteIndex >= 0 && filteredNodes[selectedAutocompleteIndex]) {{
                    selectNode(filteredNodes[selectedAutocompleteIndex].id);
                }} else if (filteredNodes.length > 0) {{
                    selectNode(filteredNodes[0].id);
                }}
            }} else if (e.key === 'Escape') {{
                if (autocompleteList.classList.contains('visible')) {{
                    hideAutocomplete();
                }} else {{
                    clearHighlight();
                }}
                searchInput.blur();
            }}
        }});

        searchInput.addEventListener('focus', () => {{
            const query = searchInput.value.trim();
            if (query.length > 0) {{
                const results = filterNodes(query);
                renderAutocomplete(results);
            }}
        }});

        // Clear button
        searchClear.addEventListener('click', () => {{
            clearHighlight();
        }});

        // Clear highlight button
        clearHighlightBtn.addEventListener('click', () => {{
            clearHighlight();
        }});

        // Close autocomplete when clicking outside
        document.addEventListener('click', (e) => {{
            if (!e.target.closest('.search-container')) {{
                hideAutocomplete();
            }}
        }});

        // Keyboard shortcut to focus search (Ctrl+F or Cmd+F)
        document.addEventListener('keydown', (e) => {{
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {{
                e.preventDefault();
                searchInput.focus();
                searchInput.select();
            }}
            if (e.key === 'Escape' && currentHighlightedNode) {{
                clearHighlight();
            }}
        }});

        // Orphan modules click handler - navigate to module node
        document.querySelectorAll('#unlinked-modules li').forEach(li => {{
            li.addEventListener('click', () => {{
                const moduleId = li.dataset.moduleId;
                const targetNode = graphData.nodes.find(n => n.id === moduleId);
                if (targetNode) {{
                    // Zoom and pan to the node
                    const scale = 1.5;
                    svg.transition()
                        .duration(750)
                        .call(zoom.transform, d3.zoomIdentity
                            .translate(width / 2 - targetNode.x * scale, height / 2 - targetNode.y * scale)
                            .scale(scale));

                    // Highlight the node temporarily
                    node.selectAll("rect, circle")
                        .style("filter", n => n.id === moduleId ? "brightness(2) drop-shadow(0 0 10px #ff9800)" : "none");

                    // Reset highlight after 2 seconds
                    setTimeout(() => {{
                        node.selectAll("rect, circle").style("filter", "none");
                    }}, 2000);
                }}
            }});
        }});
    </script>
</body>
</html>'''


def draw_graph(modules_entities: Dict, output_path: str = None) -> None:
    """Generate interactive D3.js visualization and open in browser.

    Args:
        modules_entities: Graph data with modules and their entities.
        output_path: Path to save HTML file. Default: ./codegraph.html
    """
    graph_data = convert_to_d3_format(modules_entities)
    html_content = get_d3_html_template(graph_data)

    # Determine output path
    if output_path is None:
        output_path = os.path.join(os.getcwd(), "codegraph.html")

    # Ensure absolute path
    output_path = os.path.abspath(output_path)

    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Open in default browser
    webbrowser.open(f'file://{output_path}')

    # Import click here to avoid circular imports and only when needed
    import click
    click.echo(f"Interactive graph saved and opened in browser: {output_path}")
