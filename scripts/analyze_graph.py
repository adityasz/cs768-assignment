import argparse
import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.figure import Figure

from cglp.data import Paper, paperId


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--data", type=Path, default="data/dataset.pkl",
                        help="The path to the preprocessed dataset.")
    parser.add_argument("--stats", type=Path, default="output/stats.txt",
                        help="The path to save the statistics to.")
    parser.add_argument("--in-hist", type=Path, default="output/hist_in_deg.svg",
                        help="The path to save the in-degree histogram to.")
    parser.add_argument("--out-hist", type=Path, default="output/hist_out_deg.svg",
                        help="The path to save the out-degree histogram to.")
    parser.add_argument("--combined-hist", type=Path, default="output/hist_deg.svg",
                        help="The path to save the combined histogram to.")
    return parser.parse_args()


def create_graph(papers: dict[paperId, Paper]) -> nx.DiGraph:
    """Create a directed citation graph.

    An edge (u, v) in the graph indicates that the paper u cites the paper v.
    """
    graph = nx.DiGraph()
    for paper_id, paper in papers.items():
        graph.add_node(paper_id)
        for ref_id in paper.references:
            if ref_id in papers:
                graph.add_edge(paper_id, ref_id)
    return graph


@dataclass
class Stats:
    """Statics required by the problem statement."""
    num_edges: int
    num_isolated_nodes: int
    avg_node_deg: float
    diameter: int


def get_stats(graph: nx.DiGraph) -> Stats:
    """Get statistics required by the problem statement."""
    num_edges: int = graph.number_of_edges()
    avg_node_deg: float = num_edges / graph.number_of_nodes()
    num_isolated_nodes: int = len(list(nx.isolates(graph)))
    largest_scc = max(list(nx.strongly_connected_components(graph)), key=len)
    diameter: int = nx.diameter(graph.subgraph(largest_scc))
    return Stats(
        num_edges=num_edges,
        num_isolated_nodes=num_isolated_nodes,
        avg_node_deg=avg_node_deg,
        diameter=diameter
    )


def get_deg_hist(graph: nx.DiGraph) -> list[Figure]:
    """Get the in- and out-degree histograms."""
    in_degs: list[int] = [d for n, d in graph.in_degree()]   # type: ignore # pyright/python/networkx issue
    out_degs: list[int] = [d for n, d in graph.out_degree()] # type: ignore # pyright/python/networkx issue
    figures: list[Figure] = []
    figsize: tuple[float, float] = (6, 3)  # inches

    max_deg: int = max(max(in_degs), max(out_degs))
    bins = np.arange(0, max_deg + 2)

    for label, degs in zip(["In", "Out"], [in_degs, out_degs]):
        fig, ax = plt.subplots(figsize=figsize)
        ax.hist(degs, bins=50)
        ax.set(
            xlabel=f"{label}-degree",
            ylabel="Frequency",
            xlim=(bins[0], bins[-1])
        )
        figures.append(fig)

    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(in_degs, bins=50, alpha=0.7, label="In-degree")
    ax.hist(out_degs, bins=50, alpha=0.7, label="Out-degree")
    ax.set(
        xlabel="Degree",
        ylabel="Frequency",
        xlim=(bins[0], bins[-1])
    )
    ax.legend()
    figures.append(fig)

    return figures


def main():
    args = parse_args()

    papers: dict[paperId, Paper] = {}
    with open(args.data, 'rb') as f:
        papers = pickle.load(f)

    graph: nx.DiGraph = create_graph(papers)

    figures: list[Figure] = get_deg_hist(graph)
    for fig, path in zip(figures, [args.in_hist, args.out_hist, args.combined_hist]):
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight")

    stats: Stats = get_stats(graph)
    args.stats.parent.mkdir(parents=True, exist_ok=True)
    with open(args.stats, 'w') as f:
        json.dump(stats.__dict__, f)

    # fig, ax = plt.subplots()
    # pos = nx.spring_layout(graph, seed=42)
    # nx.draw(graph, pos, with_labels=False, node_size=10, arrowsize=5, ax=ax)
    # ax.set_title("Citation Graph")


if __name__ == "__main__":
    main()
