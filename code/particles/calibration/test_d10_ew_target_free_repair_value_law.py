#!/usr/bin/env python3
"""Validate the promoted D10 target-free repair theorem artifact."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE_PAIR_SCRIPT = ROOT / "particles" / "calibration" / "derive_d10_ew_source_transport_pair.py"
SCRIPT = ROOT / "particles" / "calibration" / "derive_d10_ew_target_free_repair_value_law.py"
OUTPUT = ROOT / "particles" / "runs" / "calibration" / "d10_ew_target_free_repair_value_law.json"


def test_d10_target_free_repair_value_law_emits_closed_source_only_quintet() -> None:
    subprocess.run([sys.executable, str(SOURCE_PAIR_SCRIPT)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(SCRIPT)], check=True, cwd=ROOT)

    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_d10_ew_target_free_repair_value_law"
    assert payload["status"] == "closed"
    assert payload["object_id"] == "EWTargetFreeRepairValueLaw_D10"
    chart = payload["repair_chart"]
    assert abs(chart["tau2_tree_exact"] - (-2.311623001746158e-4)) < 1.0e-18
    assert abs(chart["delta_n_tree_exact"] - 2.346358802434819e-4) < 1.0e-18
    quintet = payload["coherent_emitted_quintet"]
    assert abs(quintet["MW_pole"] - 80.37700001539531) < 1.0e-12
    assert abs(quintet["MZ_pole"] - 91.18797807794321) < 1.0e-12
    comparison = payload["compare_only_validation_against_frozen_surface"]
    assert abs(comparison["delta_MW_gev"]) < 2.0e-8
    assert abs(comparison["delta_MZ_gev"]) < 2.0e-8
