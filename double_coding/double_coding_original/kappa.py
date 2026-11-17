"""Inter-coder agreement for the PMAM double coding.

Usage: python kappa.py pmam_scores.csv PMAM_blind_coding_sheet.xlsx
Reports linearly and quadratically weighted Cohen's kappa, exact agreement and the list of disagreements.
Requires numpy and openpyxl.
"""
import csv
import sys
import numpy as np
from openpyxl import load_workbook


def weighted_kappa(a, b, k=5, power=1):
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        O[x, y] += 1
    W = np.abs(np.subtract.outer(np.arange(k), np.arange(k))) ** power / (k - 1) ** power
    E = np.outer(O.sum(1), O.sum(0)) / O.sum()
    return 1 - (W * O).sum() / (W * E).sum()


first = {}
with open(sys.argv[1], encoding="utf8") as f:
    for r in csv.DictReader(f):
        first[(r["jurisdiction"], r["dimension"])] = int(r["score"])
second = {}
for row in load_workbook(sys.argv[2])["Coding"].iter_rows(min_row=2, values_only=True):
    j, dim, _, lev = row[:4]
    if lev:
        second[(j, dim)] = int(str(lev).strip().upper().lstrip("L"))
keys = [k for k in first if k in second]
if len(keys) < len(first):
    print(f"Warning: {len(first) - len(keys)} cells not yet coded")
a = [first[k] for k in keys]
b = [second[k] for k in keys]
print(f"Cells compared: {len(keys)}")
print(f"Exact agreement: {100 * np.mean(np.array(a) == np.array(b)):.1f}%")
print(f"Linearly weighted kappa:    {weighted_kappa(a, b, power=1):.3f}")
print(f"Quadratically weighted kappa: {weighted_kappa(a, b, power=2):.3f}")
for k in keys:
    if first[k] != second[k]:
        print(f"  disagreement {k[0]} {k[1]}: L{first[k]} vs L{second[k]}")
