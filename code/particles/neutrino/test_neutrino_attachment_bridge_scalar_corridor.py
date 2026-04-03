#!/usr/bin/env python3
"""Guard the compare-only neutrino bridge-scalar corridor."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORRECTION_SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_bridge_correction_candidate_audit.py"
SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_attachment_bridge_scalar_corridor.py"
OUTPUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_attachment_bridge_scalar_corridor.json"


def test_neutrino_attachment_bridge_scalar_corridor() -> None:
    subprocess.run(
        [sys.executable, str(CORRECTION_SCRIPT)],
        check=True,
        capture_output=True,
        text=True,
    )
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(OUTPUT)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "saved:" in completed.stdout
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_neutrino_attachment_bridge_scalar_corridor"
    assert payload["status"] == "compare_only_cross_route_corridor"
    assert payload["proof_chain_role"] == "diagnostic_only_retired_from_theorem_lane"
    assert payload["must_not_feed_back"] is True
    assert payload["exact_target_scalar"]["symbol"] == "B_nu"
    assert payload["best_constructive_subbridge_object"]["artifact"] == "oph_defect_weighted_majorana_edge_weight_family"
    representatives = payload["primary_route_representatives"]
    assert [item["route_id"] for item in representatives] == [
        "converted_symmetric_normalizer_route",
        "core_residual_scalar_route",
        "defect_family_assisted_residual_route",
    ]
    primary = payload["primary_cross_route_corridor"]
    assert primary["contains_compare_only_target"] is True
    assert primary["relative_half_width"] < 0.002
    strongest = payload["strongest_target_containing_bridge_scalar_corridor"]
    assert strongest["source"] == "oph_neutrino_bridge_correction_candidate_audit"
    assert strongest["contains_compare_only_target"] is True
    assert strongest["relative_half_width"] < primary["relative_half_width"]
    reduced = payload["exact_reduced_correction_scalar"]
    assert reduced["symbol"] == "C_nu"
    assert reduced["compare_only_target"] > 0.99
    assert reduced["compare_only_target"] < 1.01
    assert reduced["emitted_proxy_route"]["route_id"] == "core_residual_scalar_route"
    correction_audit = payload["bridge_correction_candidate_audit"]
    assert correction_audit["artifact"] == "oph_neutrino_bridge_correction_candidate_audit"
    assert correction_audit["primary_target_containing_correction_window"]["contains_compare_only_target"] is True
    consensus = payload["shortlist_route_consensus_window"]
    assert consensus["shortlist_depth_per_route"] == 5
    assert consensus["narrowing_vs_primary_cross_route_corridor"]["is_narrower"] is True
    assert consensus["relative_half_width"] < primary["relative_half_width"]
    assert [item["route_id"] for item in consensus["selected_candidates"]] == [
        "converted_symmetric_normalizer_top_1",
        "core_residual_top_2",
        "family_assisted_top_5",
    ]
    assert consensus["contains_compare_only_target"] is False
    envelope = payload["top_candidate_envelope"]
    assert envelope["candidate_count"] == 9
    assert envelope["contains_compare_only_target"] is True
    assert envelope["relative_half_width"] < 0.004
    assert payload["promotion_guard"]["status"] == "do_not_promote"
