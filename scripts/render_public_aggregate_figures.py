#!/usr/bin/env python3
"""Regenerate two numeric result figures from frozen public aggregate JSON.

These are transparent auxiliary visualizations of the provided public summary
data, not a reproduction of all figures or the original full experiment.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "electronics" / "human_gt" / "v1" / "manuscript_v1" / "figure_source_data.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="generated_figures")
    options = parser.parse_args()
    out = ROOT / options.out
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads(SOURCE.read_text(encoding="utf-8"))

    utility = data["track_b_utility"]
    guards = utility["guard"]
    x = [point["epsilon"] for point in guards]
    y = [point["ndcg_at_10"] for point in guards]
    fig, ax = plt.subplots(figsize=(7.5, 3.9))
    ax.plot(x, y, marker="o", label="Guard")
    ax.axhline(utility["raw_ndcg_at_10"], linestyle="--", label="Raw baseline")
    ax.axhline(utility["bm25_ndcg_at_10"], linestyle=":", label="BM25 baseline")
    ax.set_xticks(x)
    ax.set_xlabel("Representation-control parameter ε")
    ax.set_ylabel("nDCG@10 (27 relevance-covered queries)")
    ax.set_title("B1 retrieval effectiveness — frozen summary values")
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out / "track_b_ndcg_public.svg")
    plt.close(fig)

    coverage = data["omf_coverage"]
    labels = coverage["pairs"]
    fig, ax = plt.subplots(figsize=(8.2, 4.1))
    for track, values in coverage["tracks"].items():
        assert len(values) == len(labels), track
        ax.plot(labels, values, marker="o", label=track)
    ax.axhline(coverage["threshold"], linestyle="--", label="Required coverage (0.95)")
    ax.set_ylim(0, 1.03)
    ax.set_ylabel("Operational-label coverage")
    ax.set_xlabel("Adjacent-ε transition")
    ax.set_title("Observed coverage: exploratory operational results")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "operational_coverage_public.svg")
    plt.close(fig)
    print("Created track_b_ndcg_public.svg and operational_coverage_public.svg")
    print("WARNING: frozen aggregate visualization only; no model rerun")


if __name__ == "__main__":
    main()
