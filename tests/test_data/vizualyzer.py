import os
from typing import Dict

import matplotlib.pyplot as plt
import networkx as nx


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


def draw_graph(modules_entities: Dict) -> None:

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
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=module_edges_all,
        edge_color="#009c2c",
        width=2,
        arrows=False,
        style="dashed",
        node_size=50,
    )
    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=sub_edges_all,
        edge_color="r",
        width=2,
        arrows=False,
        style="dashed",
    )
    for p in pos:  # raise text positions
        pos[p][1] += 0.07
    plt.show()
