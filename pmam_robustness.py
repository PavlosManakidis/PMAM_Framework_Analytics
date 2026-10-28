"""Reproduce the PMAM robustness analyses (Section 4.3) from pmam_scores.csv.

Usage: python pmam_robustness.py [pmam_scores.csv]
Requires numpy >= 1.17 (numpy.random.default_rng).
"""
import csv
import sys
import numpy as np

JUR = ["Denmark", "Belgium (Flanders)", "Italy", "Greece", "Portugal", "Ireland"]
BANDS = [(0, 8, "foundational"), (9, 16, "developing"), (17, 24, "advanced"), (25, 32, "frontier")]


def load(path):
    S = np.zeros((6, 8), dtype=int)
    with open(path, encoding="utf8") as f:
        for r in csv.DictReader(f):
            S[JUR.index(r["jurisdiction"]), int(r["dimension"][1]) - 1] = int(r["score"])
    return S


def band(t):
    return next(n for lo, hi, n in BANDS if lo <= t <= hi)


def leave_one_out(S):
    tot = S.sum(1)
    loo = np.array([tot - S[:, k] for k in range(8)]).T
    print("Equal-weight totals and leave-one-dimension-out ranges")
    for j, n in enumerate(JUR):
        print(f"  {n:20s} {tot[j]:2d}/32 ({band(tot[j])})   LOO {loo[j].min()}-{loo[j].max()}")


def random_weights(S, n=200_000, seed=42):
    rng = np.random.default_rng(seed)
    sc = rng.dirichlet(np.ones(8), n) @ S.T
    first = np.bincount(sc.argmax(1), minlength=6) / n
    print(f"Random weights, Dirichlet(1,...,1), {n:,} draws, seed {seed}")
    for j, nme in enumerate(JUR):
        print(f"  P(first) {nme:20s} {100 * first[j]:6.2f}%")
    print(f"  Flanders above Portugal in {100 * np.mean(sc[:, 1] > sc[:, 4]):.1f}% of draws")


def coding_perturbation(S, p, n=100_000, seed=42):
    rng = np.random.default_rng(seed)
    T = np.clip(S[None] + rng.choice([-1, 0, 1], size=(n, 6, 8), p=[p, 1 - 2 * p, p]), 0, 4).sum(2)
    mx, mn = T.max(1, keepdims=True), T.min(1, keepdims=True)
    sole = (T == mx) & ((T == mx).sum(1, keepdims=True) == 1)
    print(f"Coding perturbation, +/-1 level with probability {p} each way, {n:,} draws, seed {seed}")
    base = [band(t) for t in S.sum(1)]
    for j, nme in enumerate(JUR):
        same_band = np.mean([band(t) == base[j] for t in T[:, j]])
        print(f"  {nme:20s} sole first {100 * sole[:, j].mean():5.1f}%  first incl. ties {100 * (T[:, j] == mx[:, 0]).mean():5.1f}%"
              f"  lowest {100 * (T[:, j] == mn[:, 0]).mean():5.1f}%  stays {base[j]} {100 * same_band:5.1f}%")


if __name__ == "__main__":
    S = load(sys.argv[1] if len(sys.argv) > 1 else "pmam_scores.csv")
    leave_one_out(S)
    random_weights(S)
    coding_perturbation(S, 0.10)
    coding_perturbation(S, 0.20)
