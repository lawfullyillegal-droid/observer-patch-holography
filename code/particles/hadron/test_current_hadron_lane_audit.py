#!/usr/bin/env python3
"""Smoke-test the current hadron-lane audit artifact."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
FULL_SCRIPT = ROOT / "particles" / "hadron" / "derive_full_unquenched_correlator.py"
POP_SCRIPT = ROOT / "particles" / "hadron" / "derive_stable_channel_sequence_population.py"
PAYLOAD_SCRIPT = ROOT / "particles" / "hadron" / "derive_stable_channel_cfg_source_measure_payload.py"
RECEIPT_SCRIPT = ROOT / "particles" / "hadron" / "derive_runtime_schedule_receipt_n_therm_and_n_sep.py"
EVAL_SCRIPT = ROOT / "particles" / "hadron" / "derive_stable_channel_sequence_evaluation.py"
SURROGATE_SCRIPT = ROOT / "particles" / "hadron" / "derive_hadron_surrogate_execution_bridge_status.py"
GEOMETRY_SCRIPT = ROOT / "particles" / "hadron" / "derive_hadron_production_geometry_summary.py"
READINESS_SCRIPT = ROOT / "particles" / "hadron" / "derive_hadron_production_readiness_report.py"
AUDIT_SCRIPT = ROOT / "particles" / "hadron" / "derive_current_hadron_lane_audit.py"
AUDIT = ROOT / "particles" / "runs" / "hadron" / "current_hadron_lane_audit.json"


def main() -> int:
    subprocess.run([sys.executable, str(FULL_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(POP_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(PAYLOAD_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(RECEIPT_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(PAYLOAD_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(EVAL_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(SURROGATE_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(GEOMETRY_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(READINESS_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(AUDIT_SCRIPT)], check=True, cwd=ROOT)
    payload = json.loads(AUDIT.read_text(encoding="utf-8"))
    if payload.get("promotion_verdict") != "suppress_from_public_surface":
        print("hadron audit should suppress the current public hadron surface", file=sys.stderr)
        return 1
    blockers = set(payload.get("pipeline_classification", {}).get("blockers", []))
    required = {
        "stable_channel_cfg_source_measure_payload",
        "stable_channel_sequence_evaluation",
        "StableChannelForwardWindowConvergence",
        "finite_volume_resonance_and_spectrum_readout",
    }
    if not required.issubset(blockers):
        print(f"missing expected hadron blockers: {sorted(required - blockers)}", file=sys.stderr)
        return 1
    frontier = set(payload.get("minimal_closure_frontier", []))
    if {"full_unquenched_correlator", "stable_channel_sequence_population", "stable_channel_sequence_evaluation", "stable_channel_groundstate_readout", "finite_volume_resonance_and_spectrum_readout"} - frontier:
        print("hadron audit should expose the sharpened minimal closure frontier", file=sys.stderr)
        return 1
    next_artifact = payload.get("recommended_next_predictive_artifact", {}).get("name")
    if next_artifact != "production_backend_export_bundle":
        print("hadron audit should point to the production backend export bundle after the runtime receipt exists", file=sys.stderr)
        return 1
    if payload.get("pipeline_classification", {}).get("lane_status") != "execution_contract_frozen_waiting_backend_bundle":
        print("hadron audit should classify the live frontier as an execution contract waiting on the backend bundle", file=sys.stderr)
        return 1
    if payload.get("smallest_constructive_missing_object") != (
        "production backend export bundle on the seeded family with publication-complete manifest provenance and real correlator arrays"
    ):
        print("hadron audit should reduce to the backend export bundle once the receipt is explicit", file=sys.stderr)
        return 1
    readiness = payload.get("production_backend_readiness") or {}
    if readiness.get("artifact") != "oph_hadron_production_readiness_report":
        print("hadron audit should attach the backend production readiness report", file=sys.stderr)
        return 1
    if readiness.get("publication_bundle_ready") is not False:
        print("hadron audit should keep the publication bundle boundary open on the current local state", file=sys.stderr)
        return 1
    if readiness.get("smallest_backend_residual_object") != (
        "production backend export bundle on the seeded family with publication-complete manifest provenance and real correlator arrays"
    ):
        print("hadron audit should sharpen the backend-side residual beyond the generic dump wording", file=sys.stderr)
        return 1
    exact = readiness.get("exact_remaining_runtime_object") or {}
    if exact.get("name") != "production_backend_export_bundle":
        print("hadron audit should expose the machine-readable backend-bundle contract", file=sys.stderr)
        return 1
    next_missing = payload.get("pipeline_classification", {}).get("summary", {}).get("next_missing_object")
    if next_missing != "production backend export bundle on the seeded family with publication-complete manifest provenance and real correlator arrays":
        print("hadron audit summary should agree that the next missing object is the backend export bundle", file=sys.stderr)
        return 1
    if payload.get("smallest_missing_theorem_after_full_unquenched") != "StableChannelForwardWindowConvergence":
        print("hadron audit should identify forward-window convergence as the next theorem after full unquenching", file=sys.stderr)
        return 1
    notes = " ".join(payload.get("notes", []))
    if "execution-and-systematics contract" not in notes or "production backend export bundle" not in notes or "publication-complete manifest provenance" not in notes:
        print("hadron audit should describe the runtime contract, backend-bundle frontier, and sharper publication bundle boundary", file=sys.stderr)
        return 1
    surrogate = payload.get("surrogate_execution_bridge") or {}
    if surrogate.get("status") != "surrogate_hmc_execution_bridge_complete":
        print("hadron audit should surface the surrogate bridge as a separate diagnostic layer", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
