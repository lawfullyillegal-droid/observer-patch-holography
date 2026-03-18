#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit

from discrete_heatkernel_test import (
    analyze_counts,
    best_pair_layout,
    group_spec,
    parse_counts,
    run_sampler,
    s3_metrics,
    stateprep_circuit,
)
from ibm_runtime_common import ensure_dir, get_service, write_json


def calibration_circuit(num_qubits: int, basis_index: int, name: str) -> QuantumCircuit:
    qc = QuantumCircuit(num_qubits, num_qubits, name=name)
    bitstring = format(basis_index, f"0{num_qubits}b")
    for qubit, bit in enumerate(reversed(bitstring)):
        if bit == "1":
            qc.x(qubit)
    qc.measure(range(num_qubits), range(num_qubits))
    return qc


def calibration_circuits(num_qubits: int, prefix: str) -> list[QuantumCircuit]:
    return [
        calibration_circuit(num_qubits, idx, f"{prefix}_prep_{format(idx, f'0{num_qubits}b')}")
        for idx in range(2**num_qubits)
    ]


def assignment_matrix(
    counts_by_name: dict[str, dict[str, int]],
    prefix: str,
    num_qubits: int,
) -> np.ndarray:
    dim = 2**num_qubits
    matrix = np.zeros((dim, dim), dtype=float)
    for prepared_state in range(dim):
        name = f"{prefix}_prep_{format(prepared_state, f'0{num_qubits}b')}"
        counts = parse_counts(counts_by_name[name], num_qubits).astype(float)
        matrix[:, prepared_state] = counts / counts.sum()
    return matrix


def mitigate_full_distribution(counts: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    observed = counts.astype(float) / counts.sum()
    mitigated = np.linalg.pinv(matrix) @ observed
    mitigated = np.clip(mitigated, 0.0, None)
    mitigated /= mitigated.sum()
    return mitigated


def analyze_layout(
    spec: dict,
    t_value: float,
    mode: str,
    shots: int,
    transpile_seed: int,
    optimization_level: int,
    credentials_file: Path,
    backend_name: str | None,
    initial_layout: list[int] | None,
    enable_gate_twirling: bool,
    enable_measure_twirling: bool,
    enable_dynamical_decoupling: bool,
    dd_sequence_type: str,
    bootstrap_samples: int,
    rng_seed: int,
    reverse_layout_order: bool,
) -> dict:
    layout_label = "reversed_layout" if reverse_layout_order else "base_layout"
    layout = list(reversed(initial_layout)) if reverse_layout_order and initial_layout is not None else initial_layout
    main_circuit = stateprep_circuit(spec, t_value, prep_mode="generic")
    cal_prefix = f"{layout_label}_cal"
    cal_circuits = calibration_circuits(spec["num_qubits"], cal_prefix)
    circuits = [main_circuit, *cal_circuits]
    run_output, backend_used = run_sampler(
        circuits=circuits,
        mode=mode,
        shots=shots,
        transpile_seed=transpile_seed,
        optimization_level=optimization_level,
        credentials_file=credentials_file,
        backend_name=backend_name,
        initial_layout=layout,
        enable_gate_twirling=enable_gate_twirling,
        enable_measure_twirling=enable_measure_twirling,
        enable_dynamical_decoupling=enable_dynamical_decoupling,
        dd_sequence_type=dd_sequence_type,
    )

    analysis_raw = analyze_counts(
        spec=spec,
        circuit_name_fn=lambda t: f"{spec['group']}_t_{t:.2f}",
        counts_by_circuit=run_output["counts_by_name"],
        t_values=[t_value],
        bootstrap_samples=bootstrap_samples,
        rng_seed=rng_seed,
    )
    circuit_name = f"{spec['group']}_t_{t_value:.2f}"
    full_counts = parse_counts(run_output["counts_by_name"][circuit_name], spec["num_qubits"])
    matrix = assignment_matrix(run_output["counts_by_name"], cal_prefix, spec["num_qubits"])
    mitigated_full_probs = mitigate_full_distribution(full_counts, matrix)
    total = float(full_counts.sum())
    mitigated_full_counts = mitigated_full_probs * total
    physical_mitigated = mitigated_full_counts[spec["logical_indices"]]
    leakage_mitigated = float((mitigated_full_counts.sum() - physical_mitigated.sum()) / mitigated_full_counts.sum())
    mitigated_metrics = s3_metrics(
        physical_mitigated,
        leakage_mitigated,
        bootstrap_samples,
        np.random.default_rng(rng_seed + 1000),
        sign_lambda=spec["lambdas"][1],
        std_lambda=spec["lambdas"][2],
    )
    return {
        "layout_label": layout_label,
        "backend": backend_used,
        "initial_layout": layout,
        "run_metadata": run_output["run_metadata"],
        "raw_full_counts": full_counts.tolist(),
        "raw_full_probs": (full_counts / full_counts.sum()).tolist(),
        "assignment_matrix": matrix.tolist(),
        "assignment_matrix_condition_number": float(np.linalg.cond(matrix)),
        "mitigated_full_probs": mitigated_full_probs.tolist(),
        "raw_metrics": analysis_raw[circuit_name],
        "mitigated_metrics": mitigated_metrics,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run S3 layout and readout diagnostic bundle.")
    parser.add_argument("--mode", choices=["local", "hardware"], default="local")
    parser.add_argument("--local-testing", action="store_true")
    parser.add_argument("--shots", type=int, default=8192)
    parser.add_argument("--transpile-seed", type=int, default=11)
    parser.add_argument("--optimization-level", type=int, choices=[0, 1, 2, 3], default=1)
    parser.add_argument("--bootstrap-samples", type=int, default=300)
    parser.add_argument("--rng-seed", type=int, default=123)
    parser.add_argument("--backend", type=str, default=None)
    parser.add_argument("--t-value", type=float, default=0.60)
    parser.add_argument("--use-best-pair-layout", action="store_true")
    parser.add_argument("--enable-gate-twirling", action="store_true")
    parser.add_argument("--enable-measure-twirling", action="store_true")
    parser.add_argument("--enable-dynamical-decoupling", action="store_true")
    parser.add_argument("--dd-sequence-type", type=str, default="XX")
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=Path("IBM_cloud.txt"),
    )
    parser.add_argument("--outdir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "local" if args.local_testing else args.mode
    outdir = ensure_dir(args.outdir)
    spec = group_spec("s3")

    initial_layout = None
    if mode == "hardware" and args.use_best_pair_layout:
        service = get_service(args.credentials_file)
        backend = service.backend(args.backend) if args.backend else service.least_busy(
            operational=True, simulator=False, min_num_qubits=2
        )
        initial_layout = best_pair_layout(backend)
        if args.backend is None:
            args.backend = backend.name

    base = analyze_layout(
        spec=spec,
        t_value=args.t_value,
        mode=mode,
        shots=args.shots,
        transpile_seed=args.transpile_seed,
        optimization_level=args.optimization_level,
        credentials_file=args.credentials_file,
        backend_name=args.backend,
        initial_layout=initial_layout,
        enable_gate_twirling=args.enable_gate_twirling,
        enable_measure_twirling=args.enable_measure_twirling,
        enable_dynamical_decoupling=args.enable_dynamical_decoupling,
        dd_sequence_type=args.dd_sequence_type,
        bootstrap_samples=args.bootstrap_samples,
        rng_seed=args.rng_seed,
        reverse_layout_order=False,
    )
    reversed_layout = analyze_layout(
        spec=spec,
        t_value=args.t_value,
        mode=mode,
        shots=args.shots,
        transpile_seed=args.transpile_seed,
        optimization_level=args.optimization_level,
        credentials_file=args.credentials_file,
        backend_name=args.backend,
        initial_layout=initial_layout,
        enable_gate_twirling=args.enable_gate_twirling,
        enable_measure_twirling=args.enable_measure_twirling,
        enable_dynamical_decoupling=args.enable_dynamical_decoupling,
        dd_sequence_type=args.dd_sequence_type,
        bootstrap_samples=args.bootstrap_samples,
        rng_seed=args.rng_seed + 1,
        reverse_layout_order=True,
    )

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": "s3_diagnostic_bundle",
        "mode": mode,
        "backend": base["backend"],
        "t_value": args.t_value,
        "shots": args.shots,
        "optimization_level": args.optimization_level,
        "base_layout": base,
        "reversed_layout": reversed_layout,
    }
    write_json(outdir / "summary.json", summary)
    (outdir / "summary_pretty.txt").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
