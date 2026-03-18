# IBM Quantum Cloud Data

This directory contains representative raw JSON outputs from the IBM Quantum Cloud OPH benchmark bundle.

## Stage 1 Markov / Recoverability

- `stage1/ibm_marrakesh_summary.json`
  `ibm_marrakesh`, job `d6t4da6sh9gc73di7720`
- `stage1/ibm_fez_seed17_summary.json`
  `ibm_fez`, job `d6t4ejngtkcc73cm8l6g`

These files contain full Pauli-tomography reconstructions, CMI values, Petz-recovery metrics, and the qualitative fingerprint checks.

## Z3

- `z3/ibm_marrakesh_summary.json`
  `ibm_marrakesh`, job `d6t4ic790okc73et0n4g`

This is the clean reduced-sector sanity check. The main outputs are `t_from_q1`, `t_from_q2`, and their agreement across the three `t` points.

## Z5

- `z5/ibm_marrakesh_summary.json`
  `ibm_marrakesh`, job `d6t4iiv90okc73et0nbg`
- `z5/ibm_marrakesh_seed17_summary.json`
  `ibm_marrakesh`, job `d6t4rkjbjfas73fp65m0`
- `z5/ibm_fez_seed17_summary.json`
  `ibm_fez`, job `d6t4ipvgtkcc73cm8qg0`
- `z5/ibm_marrakesh_t09_highshot_summary.json`
  `ibm_marrakesh`, job `d6t50e790okc73et186g`

These files expose the measured `delta2_over_delta1` values, `phi^2` target, leakage, and the extracted `t` consistency checks.

## S3

- `s3/ibm_marrakesh_layout_diagnostic_summary.json`
  `ibm_marrakesh`, jobs `d6t5c47gtkcc73cm9pd0` and `d6t5cdvgtkcc73cm9pr0`
- `s3/ibm_marrakesh_reversed_seed17_summary.json`
  `ibm_marrakesh`, job `d6t5csmsh9gc73di8e8g`

These files show the layout-sensitive `S_3` behavior directly. The base layout sits below `2`, while the reversed layout restores the target neighborhood near `2`.

## Account Status Snapshot

- `account_status/usage_snapshot_after_s3_cleanup.json`

This is the IBM usage snapshot captured after the main `S_3` cleanup run set.
