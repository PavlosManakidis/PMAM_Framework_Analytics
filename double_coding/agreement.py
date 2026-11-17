"""Inter-coder agreement for the PMAM double coding (Section 3.2, Appendix B).

Usage: python agreement.py first_coding.csv second_coding.xlsx
  first_coding.csv  : columns jurisdiction, dimension, score (0-4) and, optionally,
                      legal_status (R/P/N) and operation (V/PV/NV).
                      For the revised coding use zenodo_package/pmam_scores.csv.
  second_coding.xlsx: the completed blind coding sheet (sheet "Coding": jurisdiction,
                      dimension, sources, level, legal status, operation, notes).
Reports raw agreement, linearly and quadratically weighted Cohen's kappa with a bootstrap
95% CI (10,000 resamples of cells, numpy.random.default_rng(42)), agreement by dimension
and by jurisdiction, the 5x5 confusion matrix, the list of disagreements and, where both
files contain it, agreement on the two-part code (raw agreement and Cohen's kappa).
"""
import csv, sys
import numpy as np
from openpyxl import load_workbook

def wkappa(a, b, k=5, power=1):
    O = np.zeros((k, k))
    for x, y in zip(a, b): O[x, y] += 1
    W = np.abs(np.subtract.outer(np.arange(k), np.arange(k))) ** power / (k - 1) ** power
    E = np.outer(O.sum(1), O.sum(0)) / O.sum()
    den = (W * E).sum()
    return 1 - (W * O).sum() / den if den > 0 else float("nan")

def nominal_kappa(a, b):
    cats = sorted(set(a) | set(b)); idx = {c: i for i, c in enumerate(cats)}
    O = np.zeros((len(cats), len(cats)))
    for x, y in zip(a, b): O[idx[x], idx[y]] += 1
    po = np.trace(O) / O.sum(); pe = (O.sum(1) @ O.sum(0)) / O.sum() ** 2
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")

first = {}
for r in csv.DictReader(open(sys.argv[1], encoding="utf8")):
    first[(r["jurisdiction"], r["dimension"])] = (int(r["score"]), r.get("legal_status"), r.get("operation"))
second = {}
for row in load_workbook(sys.argv[2])["Coding"].iter_rows(min_row=2, values_only=True):
    j, dim, _, lev = row[:4]
    lg = row[4] if len(row) > 4 else None
    op = row[5] if len(row) > 5 else None
    if lev not in (None, ""):
        second[(j, dim)] = (int(str(lev).strip().upper().lstrip("L")),
                            str(lg).strip().upper() if lg else None, str(op).strip().upper() if op else None)
keys = sorted(k for k in first if k in second)
missing = [k for k in first if k not in second]
if missing: print(f"WARNING: {len(missing)} cells not coded in the second sheet: {missing}")
a = np.array([first[k][0] for k in keys]); b = np.array([second[k][0] for k in keys])
print(f"Cells compared: {len(keys)}")
print(f"Raw agreement: {np.sum(a == b)}/{len(a)} = {100 * np.mean(a == b):.1f}%")
print(f"Within one level: {np.sum(np.abs(a - b) <= 1)}/{len(a)}")
kw = wkappa(a, b); kq = wkappa(a, b, power=2)
rng = np.random.default_rng(42); boot = []
for _ in range(10000):
    i = rng.integers(0, len(a), len(a)); boot.append(wkappa(a[i], b[i]))
lo, hi = np.nanpercentile(boot, [2.5, 97.5])
print(f"Linearly weighted kappa: {kw:.3f} (bootstrap 95% CI {lo:.3f}-{hi:.3f})")
print(f"Quadratically weighted kappa: {kq:.3f}")
print("\nAgreement by dimension (exact, cells):")
for d in [f"D{i}" for i in range(1, 9)]:
    idx = [n for n, k in enumerate(keys) if k[1] == d]
    if idx: print(f"  {d}: {np.sum(a[idx] == b[idx])}/{len(idx)}")
print("\nAgreement by jurisdiction (exact, cells):")
for j in sorted({k[0] for k in keys}):
    idx = [n for n, k in enumerate(keys) if k[0] == j]
    print(f"  {j}: {np.sum(a[idx] == b[idx])}/{len(idx)}")
O = np.zeros((5, 5), int)
for x, y in zip(a, b): O[x, y] += 1
print("\nConfusion matrix (rows: first coder L0-L4; columns: second coder L0-L4):")
for i in range(5): print("  L%d " % i + " ".join(f"{v:3d}" for v in O[i]))
print("\nDisagreements (level):")
for k in keys:
    if first[k][0] != second[k][0]: print(f"  {k[0]} {k[1]}: L{first[k][0]} vs L{second[k][0]}")
for pos, name in [(1, "Legal status"), (2, "Operation")]:
    pairs = [(first[k][pos], second[k][pos]) for k in keys if first[k][pos] and second[k][pos]]
    if pairs:
        x, y = zip(*pairs)
        agree = sum(p == q for p, q in pairs)
        print(f"\n{name}: raw agreement {agree}/{len(pairs)} = {100 * agree / len(pairs):.1f}%, Cohen's kappa {nominal_kappa(x, y):.3f}")
