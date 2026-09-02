import matplotlib.pyplot as plt 
import networkx as nx

def visualize(g, out_path="graph.png"):
    pos = nx.spring_layout(g, seed=42)
    nx.draw_networkx(g, pos, with_labels=True, node_size=500, font_size=6, arrows=True)
    plt.savefig(out_path, dpi=150)