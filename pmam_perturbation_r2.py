"""PMAM coding-perturbation analysis, second revision (Section 3.5, Section 4.3, Table 7, Table B10).

Usage:
    python pmam_perturbation_r2.py pmam_scores.csv results_r2.json

Scenarios (all probabilities PER DIRECTION, 100,000 draws each, numpy.random.default_rng(42)):
  Empirically anchored, calibrated on the revised double coding (3 of 48 cells, all at the L2/L3 boundary)
    H1  all cells, 3.125% up and 3.125% down (6.25% total)
    H2  L2/L3 boundary only, directional rates of the confusion matrix:
        L2 cells move up with 2/9 (22.2%), L3 cells move down with 1/29 (3.4%), all other cells fixed
    H3  L2/L3 boundary only, pooled rate 3/38 (7.9%) in both directions
    H4  L2/L3 boundary only, upper limit of the 95% Clopper-Pearson interval for 3/38 (21.4%)
  Stress tests
    A   10% / 10% (20% total)        C   20% / 20% (40% total)        D   10% up / 5% down (15% total)
    E   15% / 15% on D4-D7, 5% / 5% elsewhere
    F   jurisdiction-wide shock: one draw per jurisdiction shifts all its cells +1 with 5% and -1 with 5%,
        then independent noise of +1 with 5% and -1 with 5% per cell (net 9.25% per direction, 18.5% total)
    G   as F with one shock per dimension (across jurisdictions)

Boundary handling: shifts are added and the result is truncated to L0-L4, so L4 cells can only move down
and L0 cells only up. A combined shift in F and G can reach +/-2 before truncation.

Evidence-constrained runs (caps applied after truncation; a cap never moves a cell below its coded level):
  EC1  a cell may rise to L3 only if its operation code is V or PV, and to L4 only on D6-D8 from a cell coded
       R and V. Moves into L1 and L2 are not restricted.
  EC2  as EC1, without any new L4 cell.
Upward moves beyond the caps would describe changes in implementation after the cutoff, not coding errors.

Output keys in results_r2.json:
  probabilities  the per-direction and total probabilities of every scenario
  results        for every scenario and run (U = unrestricted, EC1, EC2): sole first, first incl. ties,
                 pairwise orderings, last place, band retention, frontier entry and rank-acceptability matrix
  caps_EC1, caps_EC2  the cell-level caps and the maximum total each jurisdiction can reach
  frontier_gap   points each jurisdiction lacks for the frontier band (25)
"""
import csv, json, sys
import numpy as np

J = ["Denmark", "Flanders", "Italy", "Greece", "Portugal", "Ireland"]
D = [f"D{k}" for k in range(1, 9)]
N, SEED = 100_000, 42


def load(path):
    rows = {(r["jurisdiction"], r["dimension"]): r for r in csv.DictReader(open(path, encoding="utf8"))}
    S = np.array([[int(rows[(j, d)]["score"]) for d in D] for j in J])
    LG = np.array([[rows[(j, d)]["legal_status"].strip() for d in D] for j in J])
    OP = np.array([[rows[(j, d)]["operation"].strip() for d in D] for j in J])
    return S, LG, OP


def caps(S, LG, OP):
    opev = np.isin(OP, ["V", "PV"])
    d68 = np.zeros_like(S, bool)
    d68[:, 5:8] = True
    c1 = np.where(opev, np.where(d68 & (LG == "R") & (OP == "V"), 4, 3), 2)
    c2 = np.where(opev, 3, 2)
    return np.maximum(c1, S), np.maximum(c2, S)


SC = {
    "H1": dict(kind="all", up=3 / 96, down=3 / 96, total="6.25"),
    "H2": dict(kind="boundary", up=2 / 9, down=1 / 29, total="22.2 (L2), 3.4 (L3)"),
    "H3": dict(kind="boundary", up=3 / 38, down=3 / 38, total="7.9"),
    "H4": dict(kind="boundary", up=0.2138, down=0.2138, total="21.4"),
    "A": dict(kind="all", up=0.10, down=0.10, total="20"),
    "C": dict(kind="all", up=0.20, down=0.20, total="40"),
    "D": dict(kind="all", up=0.10, down=0.05, total="15"),
    "E": dict(kind="dimension", up=[.05, .05, .05, .15, .15, .15, .15, .05], down=[.05, .05, .05, .15, .15, .15, .15, .05],
              total="30 (D4-D7), 10 (others)"),
    "F": dict(kind="jurisdiction shock", q=0.10, up=0.05, down=0.05, total="18.5"),
    "G": dict(kind="dimension shock", q=0.10, up=0.05, down=0.05, total="18.5"),
}


def simulate(S, sc, cap=None):
    n, m = S.shape
    rng = np.random.default_rng(SEED)
    X = np.repeat(S[None], N, 0)
    pu = np.zeros((n, m)); pd = np.zeros((n, m))
    if sc["kind"] == "boundary":
        pu[S == 2] = sc["up"]; pd[S == 3] = sc["down"]
    else:
        pu[:] = sc["up"]; pd[:] = sc["down"]
    if sc["kind"] in ("jurisdiction shock", "dimension shock"):
        q = sc["q"]
        if sc["kind"] == "jurisdiction shock":
            u = rng.random((N, n)); sh = (u < q / 2).astype(int) - ((u >= q / 2) & (u < q)).astype(int)
            X = X + sh[:, :, None]
        else:
            u = rng.random((N, m)); sh = (u < q / 2).astype(int) - ((u >= q / 2) & (u < q)).astype(int)
            X = X + sh[:, None, :]
    u = rng.random((N, n, m))
    X = X + (u < pu) - ((u >= pu) & (u < pu + pd))
    X = np.clip(X, 0, 4)
    if cap is not None:
        X = np.minimum(X, cap)
    return X.sum(2)


def summarise(T, tot):
    pct = lambda x: round(100 * float(np.mean(x)), 1)
    mx, mn = T.max(1), T.min(1)
    first = T == mx[:, None]
    sole = first & (first.sum(1) == 1)[:, None]
    b = np.digitize(T, [8.5, 16.5, 24.5]); b0 = np.digitize(tot, [8.5, 16.5, 24.5])
    rk = 1 + (T[:, None, :] > T[:, :, None]).sum(2)
    return {
        "sole_first": {J[i]: pct(sole[:, i]) for i in range(6)},
        "first_incl_ties": {J[i]: pct(first[:, i]) for i in range(6)},
        "Ireland_last_incl_ties": pct(T[:, 5] == mn),
        "stays_in_band": {J[i]: pct(b[:, i] == b0[i]) for i in range(6)},
        "lowest_retention_except_Ireland": min(pct(b[:, i] == b0[i]) for i in range(5)),
        "frontier": {J[i]: pct(b[:, i] == 3) for i in range(6)},
        "any_frontier": pct((b == 3).any(1)),
        "pairwise_row_ahead": {J[i]: {J[k]: pct(T[:, i] > T[:, k]) for k in range(6) if k != i} for i in range(6)},
        "Flanders_ties_Portugal": pct(T[:, 1] == T[:, 4]),
        "rank_acceptability": {J[i]: [pct(rk[:, i] == k) for k in range(1, 7)] for i in range(6)},
    }


def consistency_check(scores_path):
    """Check that the levels in pmam_scores.csv, the evidence register and the first coder's revised sheet agree."""
    import os
    base = os.path.dirname(os.path.abspath(scores_path))
    lv = {(r["jurisdiction"], r["dimension"]): r["level"] for r in csv.DictReader(open(scores_path, encoding="utf8"))}
    checks = {}
    reg = os.path.join(base, "pmam_evidence_register.csv")
    if os.path.exists(reg):
        rr = list(csv.DictReader(open(reg, encoding="utf8")))
        checks["evidence register"] = all(lv[(r["jurisdiction"], r["dimension"])] == r["level"] for r in rr) and \
            {(r["jurisdiction"], r["dimension"]) for r in rr} == set(lv)
    rev = os.path.join(base, "double_coding", "double_coding_revised", "pmam_scores_revised.csv")
    if os.path.exists(rev):
        rv = {(r["jurisdiction"], r["dimension"]): r["level"] for r in csv.DictReader(open(rev, encoding="utf8"))}
        checks["first coder revised sheet"] = rv == lv
    print("Consistency of the 48 levels:", checks)
    return checks


if __name__ == "__main__":
    consistency_check(sys.argv[1])
    S, LG, OP = load(sys.argv[1])
    tot = S.sum(1)
    c1, c2 = caps(S, LG, OP)
    out = {
        "probabilities": {k: {"kind": v["kind"], "up": v["up"], "down": v["down"], "total_percent": v["total"],
                              **({"common_shock_total": v["q"]} if "q" in v else {})} for k, v in SC.items()},
        "caps_EC1": {"cells": {J[i]: dict(zip(D, c1[i].tolist())) for i in range(6)},
                     "max_total": {J[i]: int(c1[i].sum()) for i in range(6)}},
        "caps_EC2": {"cells": {J[i]: dict(zip(D, c2[i].tolist())) for i in range(6)},
                     "max_total": {J[i]: int(c2[i].sum()) for i in range(6)}},
        "frontier_gap": {J[i]: int(25 - tot[i]) for i in range(6)},
        "results": {},
    }
    for k, sc in SC.items():
        out["results"][k] = {"U": summarise(simulate(S, sc), tot),
                             "EC1": summarise(simulate(S, sc, c1), tot),
                             "EC2": summarise(simulate(S, sc, c2), tot)}
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    print("Table 7 (unrestricted / EC1)")
    for k in SC:
        u, e = out["results"][k]["U"], out["results"][k]["EC1"]
        f = lambda key, sub=None: (f"{u[key][sub] if sub else u[key]:.1f} / {e[key][sub] if sub else e[key]:.1f}")
        print(f"{k:3s} DK sole first {f('sole_first', 'Denmark')} | IE last {f('Ireland_last_incl_ties')} | "
              f"lowest retention {f('lowest_retention_except_Ireland')} | IE stays {f('stays_in_band', 'Ireland')} | "
              f"frontier {f('any_frontier')} | EC2 frontier {out['results'][k]['EC2']['any_frontier']:.1f}")
    print("EC1 maximum totals:", out["caps_EC1"]["max_total"])
    print("Frontier gap:", out["frontier_gap"])
