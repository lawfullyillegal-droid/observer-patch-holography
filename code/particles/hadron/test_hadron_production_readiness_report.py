#!/usr/bin/env python3
"""Validate the hadron production readiness report."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "particles" / "hadron" / "derive_hadron_production_readiness_report.py"
OUTPUT = ROOT / "particles" / "runs" / "hadron" / "hadron_production_readiness_report.json"


def test_hadron_production_readiness_report_tracks_backend_bundle_boundary() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], check=True, cwd=ROOT)
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_hadron_production_readiness_report"
    assert payload["runner_available"] is True
    assert payload["runtime_receipt"]["receipt_filled"] is True
    assert payload["payload_surface"]["status"] == "law_closed_waiting_measure_realization"
    manifest = payload["backend_manifest_publication_status"]
    assert manifest["manifest_present"] is False
    assert manifest["publication_complete"] is False
    dump_status = payload["production_dump_status"]
    assert dump_status["dump_present"] is False
    assert dump_status["all_required_arrays_finite"] is False
    assert payload["publication_bundle_ready"] is False
    assert payload["smallest_backend_residual_object"] == (
        "production backend export bundle on the seeded family with publication-complete manifest provenance "
        "and real correlator arrays"
    )
    exact = payload["exact_remaining_runtime_object"]
    assert exact["name"] == "production_backend_export_bundle"
    assert exact["status"] == "open"
    assert exact["required_channels"] == ["pi_iso", "N_iso_direct", "N_iso_exchange"]
    assert exact["required_local_products_after_normalization"] == [
        "backend_correlator_dump.production.json",
        "stable_channel_sequence_evaluation.json",
        "hadron_production_closure_validation_report.json",
    ]
    assert exact["runtime_receipt_contract"] == {"N_therm": 2048.0, "N_sep": 512.0}
