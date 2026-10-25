#!/usr/bin/env python3
"""Independently recalculate frozen RANK-BASED changes from published saved ranks.

No E5 encodings, Guard transformation, or scientific input texts are used.
Checks 24 adjacent-ε cells and 28 fixed-ε cross-seed statistics.
"""
import csv
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/electronics/ranking_propagation/v1"
EPS = [0,2,4,8,16,32,64]
SEEDS = [7,13,42]
TRACKS = ["B0_anchor", "B1_anchor", "C_primary", "C_broad"]


def read_track(track):
    path = BASE / "source_rankings" / (track + "_GUARD.jsonl")
    ranks={}
    with path.open(encoding="utf-8") as f:
        for line in f:
            r=json.loads(line)
            assert r["track"]==track and r["corner"]=="GUARD"
            key=(int(r["epsilon"]),int(r["seed"]),r["query_id"])
            assert key not in ranks, ("duplicate",key)
            top=r["top_scored"]
            assert len(top)>=10 and [x["rank"] for x in top[:10]]==list(range(1,11))
            ranks[key]=tuple(x["electronics_id"] for x in top[:10])
    assert len(ranks)==630, (track,len(ranks))
    for eps in EPS:
        for seed in SEEDS:
            for query in range(1,31):
                assert (eps,seed,f"Q{query:02d}") in ranks, (track,eps,seed,query)
    return ranks


def compare_adjacent(ranks, track, summary):
    checked=0
    for e0,e1 in zip(EPS[:-1],EPS[1:]):
        cases=[]
        for seed in SEEDS:
            for i in range(1,31):
                q=f"Q{i:02d}"
                a=ranks[(e0,seed,q)]
                b=ranks[(e1,seed,q)]
                cases.append((a,b))
        ordered_changed=sum(a!=b for a,b in cases)
        set_changed=sum(set(a)!=set(b) for a,b in cases)
        flipped=sum(a[0]!=b[0] for a,b in cases)
        row=summary[(track,e0,e1)]
        assert (len(cases),ordered_changed,set_changed,flipped)==(
            int(row["transition_rows"]),
            int(row["top10_ordered_changed_count"]),
            int(row["top10_set_changed_count"]),
            int(row["top1_flip_count"])
        ), (track,e0,e1,ordered_changed,set_changed,flipped)
        checked+=1
    return checked


def compare_same_epsilon(ranks, track, summary):
    checked=0
    for eps in EPS:
        unanimously_selected=[]
        mode_share=[]
        for i in range(1,31):
            q=f"Q{i:02d}"
            top1=[ranks[(eps,seed,q)][0] for seed in SEEDS]
            counts=Counter(top1)
            unanimously_selected.append(float(len(counts)==1))
            mode_share.append(max(counts.values())/3)
        row=summary[(track,eps)]
        unanimity=sum(unanimously_selected)/30
        share=sum(mode_share)/30
        assert math.isclose(unanimity,float(row["top1_unanimous_mean"]),abs_tol=1e-10), (track,eps,"unanimity",unanimity,row["top1_unanimous_mean"])
        assert math.isclose(share,float(row["top1_mode_share_mean"]),abs_tol=1e-10), (track,eps,"mode",share,row["top1_mode_share_mean"])
        checked+=1
    return checked


def main():
    with (BASE/"scientific_results"/"ranking_pair_summary.csv").open(newline="",encoding="utf-8") as f:
        adjacent={ (r["track"],int(r["epsilon_from"]),int(r["epsilon_to"])):r for r in csv.DictReader(f)}
    with (BASE/"scientific_results"/"same_epsilon_seed_robustness.csv").open(newline="",encoding="utf-8") as f:
        same={ (r["track"],int(r["epsilon"])):r for r in csv.DictReader(f)}
    assert len(adjacent)==24 and len(same)==28
    all_pairs=all_same=0
    for track in TRACKS:
        ranks=read_track(track)
        all_pairs+=compare_adjacent(ranks,track,adjacent)
        all_same+=compare_same_epsilon(ranks,track,same)
        print(f"PASS {track}: 630 frozen ranking cells")
    assert all_pairs==24 and all_same==28
    print(f"PASS: {all_pairs} adjacent-ε cells and {all_same} same-ε seed cells independently matched frozen aggregate counts")
    print("NOTE: this is exact replay FROM FROZEN RANKINGS, not E5 or Guard model rerun.")


if __name__=="__main__":
    main()
