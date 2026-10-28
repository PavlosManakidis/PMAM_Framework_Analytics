"""Regenerate PMAM Figures 1-2 (600-dpi PNG) from pmam_scores.csv.

Usage: python pmam_figures.py [pmam_scores.csv] [output_dir]
Requires numpy and matplotlib.
"""
import csv
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

J = ["Denmark", "Flanders", "Italy", "Greece", "Portugal", "Ireland"]
JCSV = ["Denmark", "Belgium (Flanders)", "Italy", "Greece", "Portugal", "Ireland"]
def scores(path="pmam_scores.csv"):
    S = np.zeros((6, 8), dtype=int)
    with open(path, encoding="utf8") as f:
        for r in csv.DictReader(f):
            S[JCSV.index(r["jurisdiction"]), int(r["dimension"][1]) - 1] = int(r["score"])
    return S


COL = ["#efefef", "#f3c4c4", "#f4dc9b", "#a9d5bb", "#4e9e70"]   # L0..L4, as in the submitted heatmap
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})

def fig1(S, out):
    fig, ax = plt.subplots(figsize=(6.45, 3.29))
    cmap = ListedColormap(COL); norm = BoundaryNorm(np.arange(-0.5, 5.5, 1), cmap.N)
    im = ax.imshow(S, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(8), [f"D{i}" for i in range(1, 9)])
    ax.set_yticks(range(6), J)
    ax.set_xticks(np.arange(-.5, 8, 1), minor=True); ax.set_yticks(np.arange(-.5, 6, 1), minor=True)
    ax.grid(which="minor", color="white", lw=1.5); ax.tick_params(which="minor", length=0)
    for i in range(6):
        for j in range(8):
            ax.text(j, i, f"L{S[i, j]}", ha="center", va="center", fontsize=8, fontweight="bold",
                    color="white" if S[i, j] == 4 else "#222222")
    for s in ax.spines.values(): s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, ticks=range(5), fraction=0.035, pad=0.02)
    cb.ax.set_yticklabels(["L0", "L1", "L2", "L3", "L4"]); cb.outline.set_visible(False)
    fig.tight_layout(); fig.savefig(out, dpi=600); plt.close(fig)

def fig2(S, out):
    x = S[:, 0:4].mean(1); y = S[:, 4:7].mean(1); d8 = S[:, 7]
    mk = {"Denmark": ("D", "#1f4e79"), "Flanders": ("s", "#d35f2b"), "Italy": ("^", "#2e7d32"),
          "Greece": ("X", "#2a9fd6"), "Portugal": ("P", "#8e3b8e"), "Ireland": ("o", "#4c9a2a")}
    fig, ax = plt.subplots(figsize=(5.89, 3.40))
    # Italy and Greece may coincide; dodge horizontally for legibility (stated in the caption)
    pts = {n: [x[i], y[i]] for i, n in enumerate(J)}
    if np.allclose(pts["Italy"], pts["Greece"]):
        pts["Italy"][0] -= 0.04; pts["Greece"][0] += 0.04
    off = {"Denmark": (6, 0, "left"), "Flanders": (6, 0, "left"), "Italy": (-6, 0, "right"),
           "Greece": (6, -7, "left"), "Portugal": (-6, 0, "right"), "Ireland": (6, 0, "left")}
    for i, n in enumerate(J):
        m, c = mk[n]; px, py = pts[n]
        ax.scatter(px, py, marker=m, s=46, color=c, zorder=3, edgecolor="white", linewidth=0.5)
        dx, dy, ha = off[n]
        ax.annotate(f"{n} (D8=L{d8[i]})", (px, py), xytext=(dx, dy), textcoords="offset points",
                    ha=ha, va="center", fontsize=7.5)
    ax.set_xlim(0, 4); ax.set_ylim(0, 4); ax.set_xticks(np.arange(0, 4.01, 0.5)); ax.set_yticks(np.arange(0, 4.01, 0.5))
    ax.set_xlabel("Rights and sharing maturity (mean of D1–D4)")
    ax.set_ylabel("Market and system integration\n(mean of D5–D7)")
    ax.grid(ls="--", lw=0.5, color="#d9d9d9"); ax.set_axisbelow(True)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    fig.tight_layout(); fig.savefig(out, dpi=600); plt.close(fig)

if __name__ == "__main__":
    S = scores(sys.argv[1] if len(sys.argv) > 1 else "pmam_scores.csv")
    outdir = sys.argv[2] if len(sys.argv) > 2 else "."
    fig1(S, f"{outdir}/Figure1_PMAM_heatmap.png")
    fig2(S, f"{outdir}/Figure2_rights_vs_integration.png")
