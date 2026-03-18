#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import StatePreparation
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import SamplerV2
from qiskit_ibm_runtime.options import SamplerOptions

from ibm_runtime_common import ensure_dir, get_service, write_json


def group_spec(name: str) -> dict:
    if name == "z3":
        lambdas = [0.0, 3.0, 3.0]
        dimensions = [1.0, 1.0, 1.0]
        num_qubits = 2
        preferred_t_values = [0.3, 0.6, 0.9]
        target_ratio = 1.0
        encoding_labels = ["q0", "q1", "q2"]
        logical_indices = [0, 1, 2]
    elif name == "s3":
        lambdas = [0.0, 6.0, 3.0]
        dimensions = [1.0, 1.0, 2.0]
        num_qubits = 2
        preferred_t_values = [0.3, 0.6, 0.9]
        target_ratio = 2.0
        encoding_labels = ["triv", "sign", "std"]
        logical_indices = [0, 1, 2]
    elif name == "z5":
        phi = (1 + math.sqrt(5)) / 2
        lambda1 = 2 * (1 - math.cos(2 * math.pi / 5))
        lambda2 = 2 * (1 - math.cos(4 * math.pi / 5))
        lambdas = [0.0, lambda1, lambda2, lambda2, lambda1]
        dimensions = [1.0, 1.0, 1.0, 1.0, 1.0]
        num_qubits = 3
        preferred_t_values = [0.3, 0.6, 0.9]
        target_ratio = phi * phi
        encoding_labels = ["q0", "q1", "q2", "q3", "q4"]
        logical_indices = [0, 1, 2, 3, 4]
    else:
        raise ValueError(f"Unsupported group {name}")
    return {
        "group": name,
        "lambdas": lambdas,
        "dimensions": dimensions,
        "num_qubits": num_qubits,
        "preferred_t_values": preferred_t_values,
        "target_ratio": target_ratio,
        "encoding_labels": encoding_labels,
        "logical_indices": logical_indices,
    }


def heatkernel_probs(lambdas: list[float], t_value: float) -> np.ndarray:
    weights = np.array([math.exp(-t_value * lam) for lam in lambdas], dtype=float)
    return weights / weights.sum()


def weighted_heatkernel_probs(dimensions: list[float], lambdas: list[float], t_value: float) -> np.ndarray:
    weights = np.array(
        [dim * math.exp(-t_value * lam) for dim, lam in zip(dimensions, lambdas)],
        dtype=float,
    )
    return weights / weights.sum()


def generic_stateprep_circuit(spec: dict, t_value: float) -> QuantumCircuit:
    num_qubits = spec["num_qubits"]
    dim = 2**num_qubits
    if spec["group"] == "s3":
        probs = weighted_heatkernel_probs(spec["dimensions"], spec["lambdas"], t_value)
    else:
        probs = heatkernel_probs(spec["lambdas"], t_value)
    amps = np.zeros(dim, dtype=complex)
    for logical_index, prob in zip(spec["logical_indices"], probs):
        amps[logical_index] = math.sqrt(prob)
    qc = QuantumCircuit(num_qubits, num_qubits, name=f"{spec['group']}_t_{t_value:.2f}")
    qc.append(StatePreparation(amps), range(num_qubits))
    qc.measure(range(num_qubits), range(num_qubits))
    return qc


def tree_z5_stateprep_circuit(spec: dict, t_value: float) -> QuantumCircuit:
    probs = heatkernel_probs(spec["lambdas"], t_value)
    p0 = probs[0]
    p1 = probs[1]
    p2 = probs[2]
    theta0 = 2 * math.acos(math.sqrt(p0))
    theta1 = 2 * math.acos(math.sqrt((2 * p1) / (1 - p0)))
    qc = QuantumCircuit(3, 3, name=f"{spec['group']}_tree_t_{t_value:.2f}")
    qc.ry(theta0, 0)
    qc.cry(theta1, 0, 1)
    qc.cry(math.pi / 2, 0, 2)
    qc.measure(range(3), range(3))
    return qc


def stateprep_circuit(spec: dict, t_value: float, prep_mode: str) -> QuantumCircuit:
    if prep_mode == "generic":
        return generic_stateprep_circuit(spec, t_value)
    if prep_mode == "tree" and spec["group"] == "z5":
        tree_spec = dict(spec)
        tree_spec["logical_indices"] = [0, 1, 3, 7, 5]
        return tree_z5_stateprep_circuit(tree_spec, t_value)
    raise ValueError(f"Unsupported prep_mode={prep_mode} for group={spec['group']}")


def parse_counts(counts: dict[str, int], num_qubits: int) -> np.ndarray:
    values = np.zeros(2**num_qubits, dtype=int)
    for bitstring, count in counts.items():
        idx = int(bitstring, 2)
        values[idx] = count
    return values


def bootstrap_counts(
    counts: np.ndarray, samples: int, rng: np.random.Generator
) -> np.ndarray:
    total = int(counts.sum())
    probs = counts / total
    return rng.multinomial(total, probs, size=samples)


def fractional_t_difference(t_a: float, t_b: float) -> float:
    mean_t = (t_a + t_b) / 2.0
    if abs(mean_t) < 1e-12:
        return 0.0
    return (t_a - t_b) / mean_t


def z3_metrics(counts: np.ndarray, bootstrap_samples: int, rng: np.random.Generator) -> dict:
    physical = counts.astype(float)
    leakage = 0
    if physical.sum() <= 0:
        raise ValueError("No physical counts in Z3 sector")
    probs = (physical + 0.5) / (physical.sum() + 1.5)
    t1 = -math.log(probs[1] / probs[0]) / 3.0
    t2 = -math.log(probs[2] / probs[0]) / 3.0
    diff = abs(t1 - t2)

    boot = bootstrap_counts(counts, bootstrap_samples, rng)
    t1_samples = []
    t2_samples = []
    diff_samples = []
    for sample in boot:
        sample_phys = sample[:3].astype(float)
        sample_probs = (sample_phys + 0.5) / (sample_phys.sum() + 1.5)
        bt1 = -math.log(sample_probs[1] / sample_probs[0]) / 3.0
        bt2 = -math.log(sample_probs[2] / sample_probs[0]) / 3.0
        t1_samples.append(bt1)
        t2_samples.append(bt2)
        diff_samples.append(abs(bt1 - bt2))

    return {
        "physical_probs": probs.tolist(),
        "leakage_probability": leakage / counts.sum(),
        "t_from_q1": t1,
        "t_from_q2": t2,
        "abs_t_difference": diff,
        "bootstrap": {
            "t_from_q1_mean": float(np.mean(t1_samples)),
            "t_from_q2_mean": float(np.mean(t2_samples)),
            "abs_t_difference_mean": float(np.mean(diff_samples)),
            "abs_t_difference_ci95": [
                float(np.quantile(diff_samples, 0.025)),
                float(np.quantile(diff_samples, 0.975)),
            ],
        },
    }


def z5_metrics(
    counts: np.ndarray,
    leakage_probability: float,
    bootstrap_samples: int,
    rng: np.random.Generator,
) -> dict:
    lambda1 = 2 * (1 - math.cos(2 * math.pi / 5))
    lambda2 = 2 * (1 - math.cos(4 * math.pi / 5))
    target_ratio = lambda2 / lambda1

    physical = counts.astype(float)
    if physical.sum() <= 0:
        raise ValueError("No physical counts in Z5 sector")
    probs = (physical + 0.5) / (physical.sum() + 2.5)
    p0 = probs[0]
    p1 = (probs[1] + probs[4]) / 2.0
    p2 = (probs[2] + probs[3]) / 2.0
    delta1 = -math.log(p1 / p0)
    delta2 = -math.log(p2 / p0)
    ratio = delta2 / delta1
    t1 = delta1 / lambda1
    t2 = delta2 / lambda2
    t_diff = abs(t1 - t2)

    boot = bootstrap_counts(counts, bootstrap_samples, rng)
    ratio_samples = []
    tdiff_samples = []
    t1_samples = []
    t2_samples = []
    for sample in boot:
        sample_phys = sample[:5].astype(float)
        sample_probs = (sample_phys + 0.5) / (sample_phys.sum() + 2.5)
        sp0 = sample_probs[0]
        sp1 = (sample_probs[1] + sample_probs[4]) / 2.0
        sp2 = (sample_probs[2] + sample_probs[3]) / 2.0
        sdelta1 = -math.log(sp1 / sp0)
        sdelta2 = -math.log(sp2 / sp0)
        st1 = sdelta1 / lambda1
        st2 = sdelta2 / lambda2
        ratio_samples.append(sdelta2 / sdelta1)
        tdiff_samples.append(abs(st1 - st2))
        t1_samples.append(st1)
        t2_samples.append(st2)

    return {
        "physical_probs": probs.tolist(),
        "leakage_probability": leakage_probability,
        "delta2_over_delta1": ratio,
        "target_ratio_phi_squared": target_ratio,
        "abs_ratio_error": abs(ratio - target_ratio),
        "t_from_lambda1": t1,
        "t_from_lambda2": t2,
        "abs_t_difference": t_diff,
        "bootstrap": {
            "ratio_mean": float(np.mean(ratio_samples)),
            "ratio_ci95": [
                float(np.quantile(ratio_samples, 0.025)),
                float(np.quantile(ratio_samples, 0.975)),
            ],
            "t_from_lambda1_mean": float(np.mean(t1_samples)),
            "t_from_lambda2_mean": float(np.mean(t2_samples)),
            "abs_t_difference_mean": float(np.mean(tdiff_samples)),
            "abs_t_difference_ci95": [
                float(np.quantile(tdiff_samples, 0.025)),
                float(np.quantile(tdiff_samples, 0.975)),
            ],
        },
    }


def s3_metrics(
    counts: np.ndarray,
    leakage_probability: float,
    bootstrap_samples: int,
    rng: np.random.Generator,
    sign_lambda: float,
    std_lambda: float,
) -> dict:
    physical = counts.astype(float)
    if physical.sum() <= 0:
        raise ValueError("No physical counts in S3 sector")
    probs = (physical + 0.5) / (physical.sum() + 1.5)
    p0, psign, pstd = probs
    delta_sign = -math.log(psign / p0)
    delta_std = -math.log((pstd / 2.0) / p0)
    ratio = delta_sign / delta_std
    t_sign = delta_sign / sign_lambda
    t_std = delta_std / std_lambda
    relative_diff = fractional_t_difference(t_sign, t_std)

    boot = bootstrap_counts(counts, bootstrap_samples, rng)
    ratio_samples = []
    tdiff_samples = []
    rel_tdiff_samples = []
    t_sign_samples = []
    t_std_samples = []
    for sample in boot:
        sphys = sample.astype(float)
        sprobs = (sphys + 0.5) / (sphys.sum() + 1.5)
        sp0, spsign, spstd = sprobs
        sdelta_sign = -math.log(spsign / sp0)
        sdelta_std = -math.log((spstd / 2.0) / sp0)
        st_sign = sdelta_sign / sign_lambda
        st_std = sdelta_std / std_lambda
        ratio_samples.append(sdelta_sign / sdelta_std)
        tdiff_samples.append(abs(st_sign - st_std))
        rel_tdiff_samples.append(fractional_t_difference(st_sign, st_std))
        t_sign_samples.append(st_sign)
        t_std_samples.append(st_std)

    return {
        "physical_probs": probs.tolist(),
        "leakage_probability": leakage_probability,
        "lambda_sign": sign_lambda,
        "lambda_std": std_lambda,
        "delta_sign_over_delta_std": ratio,
        "target_ratio": 2.0,
        "abs_ratio_error": abs(ratio - 2.0),
        "t_from_sign": t_sign,
        "t_from_std": t_std,
        "abs_t_difference": abs(t_sign - t_std),
        "fractional_delta_t_over_t": relative_diff,
        "bootstrap": {
            "ratio_mean": float(np.mean(ratio_samples)),
            "ratio_ci95": [
                float(np.quantile(ratio_samples, 0.025)),
                float(np.quantile(ratio_samples, 0.975)),
            ],
            "t_from_sign_mean": float(np.mean(t_sign_samples)),
            "t_from_std_mean": float(np.mean(t_std_samples)),
            "abs_t_difference_mean": float(np.mean(tdiff_samples)),
            "abs_t_difference_ci95": [
                float(np.quantile(tdiff_samples, 0.025)),
                float(np.quantile(tdiff_samples, 0.975)),
            ],
            "fractional_delta_t_over_t_mean": float(np.mean(rel_tdiff_samples)),
            "fractional_delta_t_over_t_ci95": [
                float(np.quantile(rel_tdiff_samples, 0.025)),
                float(np.quantile(rel_tdiff_samples, 0.975)),
            ],
        },
    }


def analyze_counts(
    spec: dict,
    circuit_name_fn,
    counts_by_circuit: dict[str, dict[str, int]],
    t_values: list[float],
    bootstrap_samples: int,
    rng_seed: int,
) -> dict:
    rng = np.random.default_rng(rng_seed)
    results = {}
    for t_value in t_values:
        circuit_name = circuit_name_fn(t_value)
        counts = parse_counts(counts_by_circuit[circuit_name], spec["num_qubits"])
        physical = counts[spec["logical_indices"]]
        leakage_probability = float((counts.sum() - physical.sum()) / counts.sum())
        if spec["group"] == "z3":
            results[circuit_name] = z3_metrics(physical, bootstrap_samples, rng)
            results[circuit_name]["leakage_probability"] = leakage_probability
        elif spec["group"] == "s3":
            results[circuit_name] = s3_metrics(
                physical,
                leakage_probability,
                bootstrap_samples,
                rng,
                sign_lambda=spec["lambdas"][1],
                std_lambda=spec["lambdas"][2],
            )
        else:
            results[circuit_name] = z5_metrics(physical, leakage_probability, bootstrap_samples, rng)
    return results


def best_star_layout(backend) -> list[int] | None:
    if backend.num_qubits < 3:
        return None
    if "cz" not in backend.target.operation_names:
        return None
    cz_props = backend.target["cz"]
    meas_props = backend.target["measure"]
    neighbors = defaultdict(set)
    for (a, b), props in cz_props.items():
        if props is not None:
            neighbors[a].add(b)
    best = None
    for center, nbrs in neighbors.items():
        nbrs = sorted(nbrs)
        for i in range(len(nbrs)):
            for j in range(i + 1, len(nbrs)):
                q1, q2 = nbrs[i], nbrs[j]
                score = 0.0
                score += (cz_props[(center, q1)].error or 0.0)
                score += (cz_props[(center, q2)].error or 0.0)
                for q in [center, q1, q2]:
                    score += 5 * ((meas_props[(q,)].error or 0.0))
                candidate = (score, [center, q1, q2])
                if best is None or candidate[0] < best[0]:
                    best = candidate
    return None if best is None else best[1]


def best_pair_layout(backend) -> list[int] | None:
    if backend.num_qubits < 2:
        return None
    if "cz" not in backend.target.operation_names:
        return None
    cz_props = backend.target["cz"]
    meas_props = backend.target["measure"]
    best = None
    seen = set()
    for (a, b), props in cz_props.items():
        if props is None:
            continue
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        score = (props.error or 0.0)
        for q in key:
            score += 5 * ((meas_props[(q,)].error or 0.0))
        candidate = (score, [key[0], key[1]])
        if best is None or candidate[0] < best[0]:
            best = candidate
    return None if best is None else best[1]


def run_sampler(
    circuits: list[QuantumCircuit],
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
) -> tuple[dict, str]:
    if mode == "local":
        backend = AerSimulator()
    else:
        service = get_service(credentials_file)
        if backend_name:
            backend = service.backend(backend_name)
        else:
            backend = service.least_busy(
                operational=True, simulator=False, min_num_qubits=circuits[0].num_qubits
            )
            backend_name = backend.name

    isa = transpile(
        circuits,
        backend=backend,
        optimization_level=optimization_level,
        seed_transpiler=transpile_seed,
        initial_layout=initial_layout,
    )

    sampler_options = None
    if mode == "hardware" and (
        enable_gate_twirling
        or enable_measure_twirling
        or enable_dynamical_decoupling
    ):
        sampler_options = SamplerOptions(default_shots=shots)
        if enable_gate_twirling:
            sampler_options.twirling.enable_gates = True
        if enable_measure_twirling:
            sampler_options.twirling.enable_measure = True
        if enable_dynamical_decoupling:
            sampler_options.dynamical_decoupling.enable = True
            sampler_options.dynamical_decoupling.sequence_type = dd_sequence_type

    sampler = SamplerV2(mode=backend, options=sampler_options)
    job = sampler.run(isa, shots=shots)
    result = job.result()
    counts_by_name = {}
    for circuit, pub in zip(circuits, result):
        key = list(pub.data.keys())[0]
        counts_by_name[circuit.name] = getattr(pub.data, key).get_counts()
    return {
        "counts_by_name": counts_by_name,
        "run_metadata": {
            "mode": mode,
            "shots": shots,
            "transpile_seed": transpile_seed,
            "optimization_level": optimization_level,
            "backend_name": getattr(backend, "name", str(backend)),
            "job_id": None if mode == "local" else job.job_id(),
            "initial_layout": initial_layout,
            "sampler_options": None
            if sampler_options is None
            else {
                "gate_twirling": enable_gate_twirling,
                "measure_twirling": enable_measure_twirling,
                "dynamical_decoupling": enable_dynamical_decoupling,
                "dd_sequence_type": dd_sequence_type if enable_dynamical_decoupling else None,
            },
        },
    }, getattr(backend, "name", str(backend))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Z3, Z5, or S3 discrete heat-kernel test.")
    parser.add_argument("--group", choices=["z3", "z5", "s3"], required=True)
    parser.add_argument("--mode", choices=["local", "hardware"], default="local")
    parser.add_argument("--local-testing", action="store_true")
    parser.add_argument("--shots", type=int, default=2048)
    parser.add_argument("--transpile-seed", type=int, default=11)
    parser.add_argument("--optimization-level", type=int, choices=[0, 1, 2, 3], default=1)
    parser.add_argument("--bootstrap-samples", type=int, default=300)
    parser.add_argument("--rng-seed", type=int, default=123)
    parser.add_argument("--prep-mode", choices=["generic", "tree"], default=None)
    parser.add_argument("--backend", type=str, default=None)
    parser.add_argument("--logical-indices", type=int, nargs="+", default=None)
    parser.add_argument(
        "--reverse-layout-order",
        action="store_true",
        help="Reverse the selected physical-qubit layout order without adding logical swap gates.",
    )
    parser.add_argument(
        "--use-best-star-layout",
        action="store_true",
        help="For small 3-qubit star-like circuits, choose the best center+neighbors layout from backend calibration data.",
    )
    parser.add_argument(
        "--use-best-pair-layout",
        action="store_true",
        help="For 2-qubit circuits, choose the best pair from backend calibration data.",
    )
    parser.add_argument("--enable-gate-twirling", action="store_true")
    parser.add_argument("--enable-measure-twirling", action="store_true")
    parser.add_argument("--enable-dynamical-decoupling", action="store_true")
    parser.add_argument("--dd-sequence-type", type=str, default="XX")
    parser.add_argument(
        "--credentials-file",
        type=Path,
        default=Path("IBM_cloud.txt"),
    )
    parser.add_argument("--t-values", type=float, nargs="+", default=None)
    parser.add_argument("--outdir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode = "local" if args.local_testing else args.mode
    outdir = ensure_dir(args.outdir)
    spec = group_spec(args.group)
    if args.logical_indices is not None:
        spec["logical_indices"] = list(args.logical_indices)
    prep_mode = args.prep_mode or ("tree" if args.group == "z5" else "generic")
    t_values = args.t_values if args.t_values is not None else spec["preferred_t_values"]
    if prep_mode == "tree" and args.group == "z5":
        spec["logical_indices"] = [0, 1, 3, 7, 5]
        circuit_name_fn = lambda t: f"{spec['group']}_tree_t_{t:.2f}"
    else:
        spec["logical_indices"] = list(spec["logical_indices"])
        circuit_name_fn = lambda t: f"{spec['group']}_t_{t:.2f}"
    circuits = [stateprep_circuit(spec, t_value, prep_mode=prep_mode) for t_value in t_values]

    initial_layout = None
    if mode == "hardware" and args.use_best_star_layout and args.group == "z5" and prep_mode == "tree":
        service = get_service(args.credentials_file)
        backend = service.backend(args.backend) if args.backend else service.least_busy(
            operational=True, simulator=False, min_num_qubits=3
        )
        initial_layout = best_star_layout(backend)
        if args.backend is None:
            args.backend = backend.name
    elif mode == "hardware" and args.use_best_pair_layout and spec["num_qubits"] == 2:
        service = get_service(args.credentials_file)
        backend = service.backend(args.backend) if args.backend else service.least_busy(
            operational=True, simulator=False, min_num_qubits=2
        )
        initial_layout = best_pair_layout(backend)
        if args.backend is None:
            args.backend = backend.name
    if args.reverse_layout_order and initial_layout is not None:
        initial_layout = list(reversed(initial_layout))

    run_output, backend_name = run_sampler(
        circuits=circuits,
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
    )
    analysis = analyze_counts(
        spec=spec,
        circuit_name_fn=circuit_name_fn,
        counts_by_circuit=run_output["counts_by_name"],
        t_values=t_values,
        bootstrap_samples=args.bootstrap_samples,
        rng_seed=args.rng_seed,
    )

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "experiment": f"{args.group}_discrete_heatkernel",
        "group": args.group,
        "mode": mode,
        "backend": backend_name,
        "t_values": t_values,
        "prep_mode": prep_mode,
        "spec": spec,
        "run_metadata": run_output["run_metadata"],
        "analysis": analysis,
    }
    write_json(outdir / "summary.json", summary)
    (outdir / "summary_pretty.txt").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
