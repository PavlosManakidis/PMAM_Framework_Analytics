"""Inter-coder agreement for the PMAM double coding.

Usage: python kappa.py pmam_scores_revised.csv PMAM_blind_coding_sheet_revised.xlsx
Reports overall percentage agreement, weighted Cohen's kappa (with bootstrap 95% CIs),
confusion matrices (counts), breakdowns by dimension/jurisdiction, and agreement on legal/operation status.
Requires numpy and openpyxl.
"""
import csv
import sys
import re
from collections import defaultdict
import numpy as np
from openpyxl import load_workbook


def weighted_kappa(a, b, k=5, power=1):
    O = np.zeros((k, k))
    for x, y in zip(a, b):
        if 0 <= x < k and 0 <= y < k:
            O[x, y] += 1
    W = np.abs(np.subtract.outer(np.arange(k), np.arange(k))) ** power / (k - 1) ** power
    E = np.outer(O.sum(1), O.sum(0)) / O.sum() if O.sum() > 0 else np.zeros((k, k))
    denom = (W * E).sum()
    return 1 - (W * O).sum() / denom if denom != 0 else np.nan


def bootstrap_kappa_ci(a, b, k=5, power=1, n_boot=10000, seed=42):
    rng = np.random.default_rng(seed)
    a_arr = np.asarray(a)
    b_arr = np.asarray(b)
    n = len(a_arr)
    if n == 0:
        return (np.nan, np.nan)
    idx = rng.integers(0, n, size=(n_boot, n))
    kappas = [weighted_kappa(a_arr[i], b_arr[i], k=k, power=power) for i in idx]
    return tuple(np.nanpercentile(kappas, [2.5, 97.5]))


def confusion_matrix(a, b, k=5):
    O = np.zeros((k, k), dtype=int)
    for x, y in zip(a, b):
        if 0 <= x < k and 0 <= y < k:
            O[x, y] += 1
    return O


def categorical_confusion_matrix(a, b, categories):
    cat_to_idx = {cat: i for i, cat in enumerate(categories)}
    k = len(categories)
    O = np.zeros((k, k), dtype=int)
    for x, y in zip(a, b):
        if x in cat_to_idx and y in cat_to_idx:
            O[cat_to_idx[x], cat_to_idx[y]] += 1
    return O


# 1. Load first coder data from CSV
first = {}
first_meta = {}
with open(sys.argv[1], encoding="utf8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames or []
    status_col = next((c for c in fieldnames if "status" in c.lower()), None)
    op_col = next((c for c in fieldnames if "operat" in c.lower()), None)

    for r in reader:
        key = (r["jurisdiction"].strip(), r["dimension"].strip())
        
        score_match = re.search(r'\d+', str(r["score"]))
        if score_match:
            first[key] = int(score_match.group())
            
        first_meta[key] = {
            "status": r[status_col].strip().upper() if status_col and r.get(status_col) else None,
            "operation": r[op_col].strip().upper() if op_col and r.get(op_col) else None,
        }

# 2. Load second coder data from XLSX ('Coding' sheet)
wb = load_workbook(sys.argv[2], data_only=True)
second = {}
second_meta = {}
for row in wb["Coding"].iter_rows(min_row=2, values_only=True):
    j, dim, _, lev, l_stat, op_stat = row[:6]
    if j and dim:
        j_clean, dim_clean = str(j).strip(), str(dim).strip()
        if lev is not None and str(lev).strip() != "":
            second[(j_clean, dim_clean)] = int(str(lev).strip().upper().lstrip("L"))
        second_meta[(j_clean, dim_clean)] = {
            "status": str(l_stat).strip().upper() if l_stat else None,
            "operation": str(op_stat).strip().upper() if op_stat else None,
        }

keys = [k for k in first if k in second]
if len(keys) < len(first):
    print(f"Warning: {len(first) - len(keys)} cells not yet coded")

a = [first[k] for k in keys]
b = [second[k] for k in keys]

# 3. Overall Exact Agreement Percentages Summary (Regardless of individual values)
print("=" * 60)
print("OVERALL SAMPLE AGREEMENT PERCENTAGES")
print("=" * 60)

# Scores Exact Agreement
score_matches = sum(x == y for x, y in zip(a, b))
score_pct = (score_matches / len(keys)) * 100 if keys else 0
print(f"• Scores Exact Agreement:         {score_matches}/{len(keys)} ({score_pct:.1f}%)")

# Legal Status Exact Agreement
shared_status_keys = [k for k in keys if first_meta.get(k, {}).get("status") and second_meta.get(k, {}).get("status")]
if shared_status_keys:
    a_stat = [first_meta[k]["status"] for k in shared_status_keys]
    b_stat = [second_meta[k]["status"] for k in shared_status_keys]
    stat_matches = sum(x == y for x, y in zip(a_stat, b_stat))
    stat_pct = (stat_matches / len(shared_status_keys)) * 100
    print(f"• Legal Status Exact Agreement:   {stat_matches}/{len(shared_status_keys)} ({stat_pct:.1f}%)")

# Operation Status Exact Agreement
shared_op_keys = [k for k in keys if first_meta.get(k, {}).get("operation") and second_meta.get(k, {}).get("operation")]
if shared_op_keys:
    a_op = [first_meta[k]["operation"] for k in shared_op_keys]
    b_op = [second_meta[k]["operation"] for k in shared_op_keys]
    op_matches = sum(x == y for x, y in zip(a_op, b_op))
    op_pct = (op_matches / len(shared_op_keys)) * 100
    print(f"• Operation Status Exact Agreement: {op_matches}/{len(shared_op_keys)} ({op_pct:.1f}%)")
print("=" * 60 + "\n")

# 4. Overall statistical metrics & bootstrap 95% CIs
kw_lin = weighted_kappa(a, b, power=1)
ci_lin = bootstrap_kappa_ci(a, b, power=1)
kw_quad = weighted_kappa(a, b, power=2)
ci_quad = bootstrap_kappa_ci(a, b, power=2)

print(f"Cells compared: {len(keys)}")
print(f"Linearly weighted kappa:      {kw_lin:.3f} (95% CI: [{ci_lin[0]:.3f}, {ci_lin[1]:.3f}])")
print(f"Quadratically weighted kappa: {kw_quad:.3f} (95% CI: [{ci_quad[0]:.3f}, {ci_quad[1]:.3f}])")

# 5. Score Confusion Matrix (Rows = Coder 1, Cols = Coder 2)
cm = confusion_matrix(a, b, k=5)
print("\nScore Confusion Matrix (Rows = Coder 1, Cols = Coder 2):")
header = "      " + " ".join(f"L{i:>3}" for i in range(5))
print(header)
for i, row in enumerate(cm):
    print(f"L{i:<4} " + " ".join(f"{val:>4}" for val in row))

# 6. Agreement by Dimension
print("\nAgreement by Dimension:")
by_dim = defaultdict(list)
for k in keys:
    by_dim[k[1]].append((first[k], second[k]))

for dim, pairs in sorted(by_dim.items()):
    da, db = zip(*pairs)
    exact = 100 * np.mean(np.array(da) == np.array(db))
    k_lin = weighted_kappa(da, db, power=1)
    print(f"  {dim:<10} n={len(pairs):<3} exact={exact:5.1f}%  kw_lin={k_lin:.3f}")

# 7. Agreement by Jurisdiction
print("\nAgreement by Jurisdiction:")
by_jur = defaultdict(list)
for k in keys:
    by_jur[k[0]].append((first[k], second[k]))

for jur, pairs in sorted(by_jur.items()):
    ja, jb = zip(*pairs)
    exact = 100 * np.mean(np.array(ja) == np.array(jb))
    k_lin = weighted_kappa(ja, jb, power=1)
    print(f"  {jur:<15} n={len(pairs):<3} exact={exact:5.1f}%  kw_lin={k_lin:.3f}")

# Helper function to print categorical confusion matrices (counts only)
def report_categorical_agreement(title, field_name, categories):
    print(f"\n--- {title} ---")
    shared = [k for k in keys if first_meta.get(k, {}).get(field_name) and second_meta.get(k, {}).get(field_name)]
    if not shared:
        print(f"  No valid data found for {field_name}.")
        return

    a_cat = [first_meta[k][field_name] for k in shared]
    b_cat = [second_meta[k][field_name] for k in shared]

    cm_counts = categorical_confusion_matrix(a_cat, b_cat, categories)
    header = "      " + " ".join(f"{c:>6}" for c in categories)
    
    print("Confusion Matrix (Counts - Rows = Coder 1, Cols = Coder 2):")
    print(header)
    for i, row in enumerate(cm_counts):
        print(f"{categories[i]:<5} " + " ".join(f"{val:>6}" for val in row))

    # Print disagreements
    for k in shared:
        v1 = first_meta[k][field_name]
        v2 = second_meta[k][field_name]
        if v1 != v2:
            print(f"  disagreement {k[0]} {k[1]} ({field_name}): '{v1}' vs '{v2}'")

# 8. Legal Status Confusion Matrix & Disagreements
report_categorical_agreement("Legal Status Agreement Matrix", "status", ["R", "P", "N"])

# 9. Operation Status Confusion Matrix & Disagreements
report_categorical_agreement("Operation Status Agreement Matrix", "operation", ["V", "PV", "NV"])

# 10. Cell-level score disagreements
print("\nCell Score Disagreements:")
for k in keys:
    if first[k] != second[k]:
        print(f"  disagreement {k[0]} {k[1]}: L{first[k]} vs L{second[k]}")