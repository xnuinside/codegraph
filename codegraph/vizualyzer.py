import csv
import json
import logging
import os
import webbrowser
from typing import Dict, List

logger = logging.getLogger(__name__)


def process_module_in_graph(module: Dict[str, list], module_links: list, G):
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
    try:
        import matplotlib.pyplot as plt
        import networkx as nx
    except ImportError:
        raise ImportError(
            "matplotlib is required for matplotlib visualization. "
            "Install it with: pip install codegraph[matplotlib]"
        )

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


def convert_to_d3_format(modules_entities: Dict, entity_metadata: Dict = None) -> Dict:
    """Convert the modules_entities graph data to D3.js format."""
    nodes: List[Dict] = []
    links: List[Dict] = []
    node_ids = set()
    module_links = set()  # Track module-to-module links
    module_full_paths: Dict[str, str] = {}  # Map module name to full path

    if entity_metadata is None:
        entity_metadata = {}

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
        module_metadata = entity_metadata.get(module_path, {})

        # Compute relative path from common root
        if common_root:
            relative_path = os.path.relpath(module_path, common_root)
        else:
            relative_path = module_path

        module_full_paths[module_name] = relative_path

        # Calculate total lines in module
        total_lines = sum(m.get("lines", 0) for m in module_metadata.values())

        # Add module node
        if module_name not in node_ids:
            nodes.append({
                "id": module_name,
                "type": "module",
                "collapsed": False,
                "fullPath": relative_path,
                "lines": total_lines
            })
            node_ids.add(module_name)

        # Add entity nodes and build mapping
        for entity_name in entities.keys():
            entity_id = f"{module_name}:{entity_name}"
            entity_to_module[entity_name] = module_name
            entity_to_module[f"{module_name.replace('.py', '')}.{entity_name}"] = module_name

            # Get entity metadata
            ent_meta = module_metadata.get(entity_name, {})
            lines = ent_meta.get("lines", 0)
            entity_type = ent_meta.get("entity_type", "function")

            if entity_id not in node_ids:
                nodes.append({
                    "id": entity_id,
                    "label": entity_name,
                    "type": "entity",
                    "parent": module_name,
                    "lines": lines,
                    "entityType": entity_type
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


def _get_template_dir() -> str:
    """Get the path to the templates directory."""
    return os.path.join(os.path.dirname(__file__), 'templates')


def _read_template_file(filename: str) -> str:
    """Read a template file from the templates directory."""
    template_path = os.path.join(_get_template_dir(), filename)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_d3_html_template(graph_data: Dict) -> str:
    """Generate HTML with embedded D3.js visualization."""
    graph_json = json.dumps(graph_data, indent=2)

    # Read template files
    html_template = _read_template_file('index.html')
    css_content = _read_template_file('styles.css')
    js_content = _read_template_file('main.js')

    # Replace placeholders
    html_content = html_template.replace('/* STYLES_PLACEHOLDER */', css_content)
    html_content = html_content.replace('/* GRAPH_DATA_PLACEHOLDER */', graph_json)
    html_content = html_content.replace('/* SCRIPT_PLACEHOLDER */', js_content)

    return html_content


def draw_graph(modules_entities: Dict, entity_metadata: Dict = None, output_path: str = None) -> None:
    """Generate interactive D3.js visualization and open in browser.

    Args:
        modules_entities: Graph data with modules and their entities.
        entity_metadata: Metadata for entities (lines of code, type).
        output_path: Path to save HTML file. Default: ./codegraph.html
    """
    graph_data = convert_to_d3_format(modules_entities, entity_metadata)
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


def export_to_csv(modules_entities: Dict, entity_metadata: Dict = None, output_path: str = None) -> None:
    """Export graph data to CSV file.

    Args:
        modules_entities: Graph data with modules and their entities.
        entity_metadata: Metadata for entities (lines of code, type).
        output_path: Path to save CSV file. Default: ./codegraph.csv
    """
    import click

    # Get D3 format data to reuse link calculation logic
    graph_data = convert_to_d3_format(modules_entities, entity_metadata)
    nodes = graph_data["nodes"]
    links = graph_data["links"]

    # Build links_in and links_out counts
    links_out: Dict[str, int] = {}
    links_in: Dict[str, int] = {}

    for link in links:
        source = link["source"]
        target = link["target"]
        link_type = link.get("type", "")

        # Skip module-entity links (structural, not dependency)
        if link_type == "module-entity":
            continue

        links_out[source] = links_out.get(source, 0) + 1
        links_in[target] = links_in.get(target, 0) + 1

    # Determine output path
    if output_path is None:
        output_path = os.path.join(os.getcwd(), "codegraph.csv")

    output_path = os.path.abspath(output_path)

    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'type', 'parent_module', 'full_path', 'links_out', 'links_in', 'lines']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for node in nodes:
            node_id = node["id"]
            node_type = node.get("type", "")

            # Determine display type
            if node_type == "module":
                display_type = "module"
                parent_module = ""
                full_path = node.get("fullPath", "")
                lines = node.get("lines", 0)
                name = node_id
            elif node_type == "entity":
                display_type = node.get("entityType", "function")
                parent_module = node.get("parent", "")
                # Find full path from parent module
                full_path = ""
                for n in nodes:
                    if n["id"] == parent_module and n["type"] == "module":
                        full_path = n.get("fullPath", "")
                        break
                lines = node.get("lines", 0)
                name = node.get("label", node_id)
            else:  # external
                display_type = "external"
                parent_module = ""
                full_path = ""
                lines = 0
                name = node.get("label", node_id)

            writer.writerow({
                'name': name,
                'type': display_type,
                'parent_module': parent_module,
                'full_path': full_path,
                'links_out': links_out.get(node_id, 0),
                'links_in': links_in.get(node_id, 0),
                'lines': lines
            })

    click.echo(f"Graph data exported to CSV: {output_path}")
