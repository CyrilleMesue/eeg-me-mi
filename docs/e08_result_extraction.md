# E08 result extraction (protocol-confound diagnostic)

These tables **characterize** fixed-order / drift patterns. They do **not** remove the run-order confound.

- by_run rows: 12; columns: ['run', 'condition', 'task_family', 'repetition', 'n_epochs', 'precue_mu_mean', 'precue_beta_mean', 'ptp_mean']
- by_repetition rows: 12; columns: ['condition', 'task_family', 'repetition', 'n_epochs', 'precue_mu_mean', 'precue_beta_mean', 'ptp_mean']
- matched_pairs rows: 6; columns: ['pair_id', 'me_run', 'mi_run', 'n_me', 'n_mi', 'precue_mu_me', 'precue_mu_mi', 'precue_beta_me', 'precue_beta_mi', 'ptp_me', 'ptp_mi']
