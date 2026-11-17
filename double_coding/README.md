# Double coding

- `double_coding_original/`: the original independent coding of the submitted version (first coder's levels in `pmam_scores.csv`, second coder's completed sheet, `kappa.py`). Result: 44 of 48 cells (91.7%), linearly weighted kappa 0.899.
- `double_coding_revised/`: the blind coding of the revised version against the revised anchors (first coder's revised levels and two-part codes in `pmam_scores_revised.csv`, second coder's completed sheet, `kappa_revised.py`). Result: 45 of 48 cells (93.8%), linearly weighted kappa 0.922 (bootstrap 95% CI 0.811–1.000), quadratically weighted kappa 0.953. Legal status 41 of 48 (85.4%), operation 41 of 48 (85.4%).
- `agreement.py`: alternative script that also reports Cohen's kappa for the two-part code (legal status 0.485, operation 0.709).

Run, for example:
python double_coding_revised/kappa_revised.py double_coding_revised/pmam_scores_revised.csv double_coding_revised/PMAM_blind_coding_sheet_revised.xlsx
