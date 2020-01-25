import os
from typing import Dict
import matplotlib.pyplot as plt
import networkx as nx


def draw_graph(modules_entities: Dict) -> None:
    gr = nx.Graph()
    module_edges = []
    sub_edges = []
    for module in modules_entities:
        for entity in modules_entities[module]:
            module_edges.append((os.path.basename(module), entity))
            for dep in modules_entities[module][entity]:
                if '.' in dep:
                    dep = dep.split('.')[1].replace('.', '.py')
                sub_edges.append((entity, dep))
        gr.add_edges_from(module_edges)
        gr.add_edges_from(sub_edges)
    pos = nx.spring_layout(gr)
    nx.draw(gr, pos, font_size=12, with_labels=False)
    for p in pos:  # raise text positions
        pos[p][1] += 0.07
    nx.draw_networkx_labels(gr, pos)
    plt.show()
