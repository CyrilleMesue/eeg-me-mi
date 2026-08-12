# EEGMMIDB local data-access report

Date: 2026-08-12  
Test scope: subjects 1–2, runs 3–4 only. This is a mechanical access test, not a scientific analysis.

## Environment and cache

- Python: 3.14.4
- MNE: 1.12.1
- Access method: `mne.datasets.eegbci.load_data()` followed by `mne.io.read_raw_edf()`
- Persistent cache: `data/physionet_eegmmidb/MNE-eegbci-data/files/eegmmidb/1.0.0/`
- Cache size after test: approximately 9.9 MB
- The four EDF files were absent before the test, downloaded once from PhysioNet, and retained. Future calls with the same path should reuse them.

The cache location is explicit and uses `update_path=False`, avoiding a hidden global path change. It should later become a configurable dataset root outside result directories.

## Protocol assertions

- Run 3 was treated as motor execution; run 4 as motor imagery.
- T1/T2 were extracted as within-run movement cues, never as ME/MI labels.
- For these unilateral runs, T1 means left fist and T2 means right fist.
- All recordings contained T0, T1, and T2 annotations.

## Results

| Subject | Run | Condition | Original Hz | EEG channels | T0 | T1 | T2 | T1/T2 events | Kept at 200 µV | Status |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 3 | ME | 160 | 64 | 15 | 8 | 7 | 15 | 13 | Pass |
| 1 | 4 | MI | 160 | 64 | 15 | 8 | 7 | 15 | 13 | Pass |
| 2 | 3 | ME | 160 | 64 | 15 | 8 | 7 | 15 | 14 | Pass |
| 2 | 4 | MI | 160 | 64 | 15 | 7 | 8 | 15 | 15 | Pass |

Overall, 55/60 epochs survived the illustrative 200 µV rule. These counts must not be used to select that threshold.

## Preprocessing validation

For every file, the test successfully:

1. loaded EDF data with preload;
2. confirmed 160 Hz and 64 EEG channels;
3. standardized EEGBCI channel names;
4. attached the `standard_1005` montage without missing-channel errors;
5. found all 21 required FC/C/CP sensorimotor channels;
6. applied average reference;
7. resampled to exactly 80 Hz;
8. filtered 8–30 Hz;
9. extracted 15 T1/T2 events;
10. formed -2.0 to 3.5 s epochs with 441 samples each; and
11. applied a declared 200 µV peak-to-peak rejection threshold.

Expected sensorimotor set confirmed: FC5/3/1/z/2/4/6, C5/3/1/z/2/4/6, and CP5/3/1/z/2/4/6.

## Interpretation and limits

Data access, annotations, channel standardization, sampling, event extraction, and the proposed preprocessing mechanics work locally. This test does not establish that all 109 subjects are complete, that 200 µV is optimal, that the scientific pipeline is leakage-free end-to-end, or that full-cohort memory/runtime is acceptable.

The five rejected epochs already demonstrate why condition-, movement-, run-, and participant-level rejection reporting is necessary. The full toy validation must test all task families and include runs 5–6 so the bilateral T1/T2 mapping is exercised.

## Reproducibility note

The access-test environment is intentionally isolated in `.venv-data-access/`; it is not the final project environment. The eventual repository should pin Python and exact package versions and snapshot them in each run. No EDF should be committed to Git or copied into each experiment directory.

