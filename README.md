# PMAM dataset and code (version 1.2, second revision)

DOI: https://doi.org/10.5281/zenodo.24322087

Data and code for "Bridging the Gap between Prosumer Rights and Market Access: Monitoring Citizen Participation in Europe’s Sustainable Electricity Markets" (Dourbois, Manakidis, Biskas; *Sustainability*, revised manuscript, second revision, November 2026). Regulatory cutoff: 31 August 2026.

## Contents

- `pmam_scores.csv` — the 48 jurisdiction–dimension levels (L0–L4) with the two-part code (legal status R/P/N; operational verification V/PV/NV), rationale and sources (Appendix A of the article).
- `pmam_evidence_register.csv` — one row per cell and source: reference number, full citation, URL, evidence date, access date, pinpoint reference and archived copy.
- `references.txt` — the numbered reference list of the article (numbers used in the two CSV files).
- `pmam_robustness.py` — reproduces Tables 5 and 6, the alternative band thresholds, Tables B1–B4 and the unrestricted stress scenarios A–G (leave-one-dimension-out, random Dirichlet(1,…,1) weights with 200,000 draws, convex and concave level mappings, non-compensatory rules and weak dominance). Output: `results.json`.
- `pmam_perturbation_r2.py` — reproduces Table 7 and Table B10 of the second revision: empirically anchored scenarios H1–H4 and stress tests A, C–G, each unrestricted and evidence-constrained (EC1, EC2). It also checks that the 48 levels in `pmam_scores.csv`, the evidence register and the first coder's revised sheet are identical. Output: `results_r2.json` (keys `probabilities`, `results`, `caps_EC1`, `caps_EC2`, `frontier_gap`).
- `pmam_figures.py` — regenerates Figures 1 and 2 (600 dpi PNG).

The `snapshots/` — archived copies (PDF) of the sources listed in the evidence register, saved on 17 November 2026 can be found in https://doi.org/10.5281/zenodo.24333748. Files are named after the reference number (`ref47.pdf` for reference [47]). Where a reference covers several acts, the further acts are in additional files (`ref54b.pdf`, `ref74_1.pdf` to `ref74_3.pdf`). Web pages were printed with their URL and access date in the page header. Legal acts are archived as the official or consolidated text.

In `pmam_evidence_register.csv`, the column `pinpoint` gives the article, section or page that supports the cell, and `archived_copy` gives the file in `snapshots/`.

## Usage

```
pip install numpy matplotlib openpyxl
python pmam_robustness.py pmam_scores.csv results.json
python pmam_perturbation_r2.py pmam_scores.csv results_r2.json
python pmam_figures.py pmam_scores.csv .
```

## Where each result comes from

| Article | File and key |
|---|---|
| Table 4, Appendix A | `pmam_scores.csv` |
| Evidence for each of the 48 scores | `pmam_evidence_register.csv` (with `snapshots/`) |
| Tables 5 and 6, alternative bands, Tables B1 and B2 | `pmam_robustness.py` → `results.json` |
| Tables B3 and B4 (scenario A, unrestricted) | `pmam_robustness.py` → `results.json` (`perturb`) |
| Table 7 (H1–H4 and A, C–G, unrestricted / EC1) | `pmam_perturbation_r2.py` → `results_r2.json` (`results`, runs `U` and `EC1`) |
| Table B10 (H1 and H2, EC1) | `results_r2.json` (`results` → `H1`/`H2` → `EC1` → `rank_acceptability`, `stays_in_band`) |
| Tables B5–B9 | `double_coding/` |

## Coding-perturbation scenarios

- **Probabilities** are per direction. A cell away from the ends of the scale with p_up and p_down changes level with total probability p_up + p_down.
- **Empirically anchored scenarios** use the revised double coding (3 of 48 cells, all at the L2/L3 boundary: 2 of the 9 L2 cells were coded L3 by the second coder and 1 of the 29 L3 cells was coded L2). H1: 3.125% / 3.125% on all cells (6.25% total). H2: L2/L3 boundary only, directional rates 2/9 = 22.2% up from L2 and 1/29 = 3.4% down from L3. H3: L2/L3 boundary only, pooled 3/38 = 7.9% in both directions. H4: as H3 at the upper limit of the 95% Clopper–Pearson interval for 3/38 (21.4%). In H2–H4 all other cells are fixed.
- **Stress tests**: A 10% / 10% (20% total), C 20% / 20% (40%), D 10% up / 5% down (15%), E 15% / 15% on D4–D7 and 5% / 5% elsewhere, F jurisdiction-wide shock and G dimension-wide shock. In F (G) one draw per jurisdiction (dimension) shifts all its cells by +1 with probability 5% and by −1 with probability 5%, and independent noise of ±1 with 5% in each direction is then added per cell (net 9.25% per direction, 18.5% total). The combined shift can reach ±2 before truncation.
- **Boundary handling**: shifts are added and the result is truncated to L0–L4, so L4 cells can only move down and L0 cells only up.
- **Evidence caps** (applied after truncation, never below the coded level): EC1 allows a rise to L3 only for cells with operation V or PV and to L4 only on D6–D8 from cells coded R and V. Moves into L1 and L2 are not restricted. EC2 additionally allows no new L4 cell. The caps per cell and the resulting maximum totals are written to `results_r2.json`.
- **Random generator**: `numpy.random.default_rng(42)`, 100,000 draws per scenario and run.

## Licence

Data: CC BY 4.0. Code: MIT.

## Funding

EU-DREAM project (Effective Uptake of Digital Services to Repower European Consumers and Communities as Active Participants in Energy Transition and Markets), European Union's Horizon Europe programme, grant agreement No. 101160614.
