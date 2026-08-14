# E03 result extraction (factual)

- Source: `results/definitive/full/e03` (immutable definitive).
- ROI summary rows: 6
- Channel FDR rows: 42
- Laterality rows: 408

## ROI summary columns

band, roi, n, mean, std, participant_effect_p2.5, participant_effect_p97.5, mean_bootstrap_ci_low, mean_bootstrap_ci_high, p_uncorrected, fdr_family, p_fdr, reject_fdr

## Notes

- `participant_effect_p2.5` / `p97.5` are participant-effect **distribution percentiles**, not CIs for the mean.
- `mean_bootstrap_ci_low` / `mean_bootstrap_ci_high` are bootstrap CIs for the mean effect.
- No biological conclusions in this extraction.

## ROI summary (verbatim)

```
band                roi   n      mean      std  participant_effect_p2.5  participant_effect_p97.5  mean_bootstrap_ci_low  mean_bootstrap_ci_high  p_uncorrected fdr_family        p_fdr  reject_fdr
beta  left_sensorimotor 102 -0.978276 0.840398                -3.448185                  0.189409              -1.145402               -0.821703   4.572647e-17  roi_level 1.371794e-16        True
beta            midline 102 -0.998082 0.858650                -2.992912                  0.269382              -1.164242               -0.832487   8.054733e-17  roi_level 1.610947e-16        True
beta right_sensorimotor 102 -1.118445 0.850724                -3.371669                  0.115511              -1.290721               -0.954903   2.981956e-17  roi_level 1.371794e-16        True
  mu  left_sensorimotor 102 -0.927106 1.007497                -2.927824                  0.870883              -1.126902               -0.724296   1.200440e-12  roi_level 1.440528e-12        True
  mu            midline 102 -0.707280 0.909323                -2.470644                  1.072762              -0.886381               -0.528610   8.204660e-12  roi_level 8.204660e-12        True
  mu right_sensorimotor 102 -1.048640 1.038508                -3.166013                  0.680985              -1.250752               -0.843931   8.930439e-14  roi_level 1.339566e-13        True
```

