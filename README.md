# PMAM dataset and code (revised version)

Data and code for "Bridging the Gap between Prosumer Rights and Market Access: A Comparative Assessment of European Regulatory Frameworks" (Dourbois, Manakidis, Biskas; *Sustainability*, revised manuscript, November 2026). Regulatory cutoff: 31 August 2026.

## Contents

- `pmam_scores.csv` — the 48 jurisdiction–dimension levels (L0–L4) with the two-part code (legal status R/P/N; operational verification V/PV/NV), rationale and sources (Appendix A of the article).
- `pmam_evidence_register.csv` — one row per cell and source: reference number, full citation, URL, evidence date, access date, pinpoint reference and archived copy.
- `references.txt` — the numbered reference list of the article (numbers used in the two CSV files).
- `pmam_robustness.py` — reproduces Section 4.3, Tables 5–7 and Appendix B: leave-one-dimension-out; random Dirichlet(1,…,1) weights (200,000 draws) with rank-acceptability matrix and pairwise probabilities; convex and concave level mappings; non-compensatory rules (count of L3+ cells, minimum level, leximin) and weak dominance; alternative band thresholds; seven coding-perturbation scenarios (100,000 draws each). All draws use `numpy.random.default_rng(42)`.
- `results.json` — output of `pmam_robustness.py`.
- `pmam_figures.py` — regenerates Figures 1 and 2 (600 dpi PNG).
- `snapshots/` — archived copies (PDF) of the web sources listed in the evidence register.

## Usage

```
pip install numpy matplotlib openpyxl
python pmam_robustness.py pmam_scores.csv results.json
python pmam_figures.py pmam_scores.csv .
```

The double-coding material is in `double_coding/`: the original and the revised independent codings, each with the first coder's levels, the second coder's completed sheet and the script that computes the agreement (see `double_coding/README.md`).

## Licence

Data: CC BY 4.0. Code: MIT.

## Funding

EU-DREAM project (Effective Uptake of Digital Services to Repower European Consumers and Communities as Active Participants in Energy Transition and Markets), European Union's Horizon Europe programme, grant agreement No. 101160614.
