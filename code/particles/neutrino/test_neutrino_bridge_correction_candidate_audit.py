#!/usr/bin/env python3
"""Guard the reduced neutrino bridge-correction audit."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_bridge_correction_candidate_audit.py"
OUTPUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_bridge_correction_candidate_audit.json"


def test_neutrino_bridge_correction_candidate_audit() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(OUTPUT)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "saved:" in completed.stdout
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_neutrino_bridge_correction_candidate_audit"
    assert payload["status"] == "compare_only_reduced_bridge_correction_search"
    assert payload["proof_chain_role"] == "diagnostic_only_retired_from_theorem_lane"
    assert payload["must_not_feed_back"] is True
    exact = payload["exact_target_scalar"]
    assert exact["symbol"] == "C_nu"
    assert exact["bridge_reconstruction"] == "B_nu = (I_nu^0.5 * ratio_hat^0.5 * sum_defect^-1) * C_nu"
    target = payload["current_compare_only_target"]
    assert 0.99 < target["value"] < 1.01
    assert payload["best_normalizer_quotient_candidate"]["route_id"] == "normalizer_quotient_top_1"
    assert payload["best_core_correction_candidate"]["formula"] == "I_nu^-1 * ratio_hat^0.5 * gamma^0.5"
    assert payload["best_family_assisted_correction_candidate"]["formula"] == "sum_gap^2 * prod_qbar * solar_response_over_mstar^-0.5"
    primary = payload["primary_target_containing_correction_window"]
    assert primary["contains_compare_only_target"] is True
    assert primary["relative_half_width"] < 0.0011
    assert [item["route_id"] for item in primary["selected_candidates"]] == [
        "core_correction_top_3",
        "family_correction_top_1",
    ]
    induced = payload["induced_target_containing_bridge_scalar_window"]
    assert induced["contains_compare_only_target"] is True
    assert induced["relative_half_width"] < 0.0011
    supporting = payload["supporting_three_route_target_containing_correction_window"]
    assert supporting["contains_compare_only_target"] is True
    assert supporting["candidate_count"] == 3
    assert payload["hard_guard"]["status"] == "do_not_promote"
