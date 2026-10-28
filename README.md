# PMAM dataset and code

Data and code for "Bridging the Gap between Prosumer Rights and Market Access: A Comparative Assessment of European Regulatory Frameworks" (Dourbois, Manakidis, Biskas; submitted to *Sustainability*).

## Contents

- `pmam_scores.csv` — the 48 jurisdiction–dimension scores (L0–L4). 
- `pmam_robustness.py` — reproduces Section 4.3: leave-one-dimension-out ranges, random weights (Dirichlet(1,…,1), 200,000 draws) and ordinal coding perturbation (±1 level, p = 0.10 and 0.20 per direction, 100,000 draws). All draws use `numpy.random.default_rng(42)`.
- `pmam_figures.py` — regenerates Figures 1 and 2 as 600-dpi PNG.

## Usage

```
pip install numpy matplotlib
python pmam_robustness.py pmam_scores.csv
python pmam_figures.py pmam_scores.csv .
```

