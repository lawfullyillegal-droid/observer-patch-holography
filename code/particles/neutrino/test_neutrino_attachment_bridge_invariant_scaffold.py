#!/usr/bin/env python3
"""Guard the corrected neutrino bridge-invariant scaffold."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_attachment_bridge_invariant_scaffold.py"
OUTPUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_attachment_bridge_invariant_scaffold.json"


def test_neutrino_attachment_bridge_invariant_scaffold() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(OUTPUT)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "saved:" in completed.stdout
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_neutrino_attachment_bridge_invariant_scaffold"
    assert payload["bridge_factor_schema"] == "B_nu = lambda_nu * q_mean^p_nu / m_star_eV"
    assert payload["residual_invariant_symbol"] == "B_nu"
    assert payload["contract"]["must_emit"].startswith("one positive non-homogeneous residual attachment scalar B_nu")
    assert payload["contract"]["must_imply"] == "lambda_nu = (m_star_eV / q_mean^p_nu) * B_nu"
    ruled_out = payload["ruled_out_current_selected_point_scalar"]
    assert ruled_out["status"] == "already_internal_to_current_emitted_stack_not_the_missing_bridge_scalar"
    assert ruled_out["selected_point"] == "weighted_cycle_selector_psi_wc"
    assert payload["qbar_only_collapse_status"] == "refuted_on_current_attached_stack_by_attachment_irreducibility_theorem"
    constructive = payload["best_constructive_subbridge_object"]
    assert constructive["artifact"] == "oph_defect_weighted_majorana_edge_weight_family"
    assert constructive["status"] == "closed_constructive_subbridge_object"
    assert constructive["raw_edge_score_rule"] == "q_e = sqrt(gap_e * defect_e)"
    assert "B_nu = lambda_nu * q_mean^p_nu / m_star_eV" in payload["residual_attachment_quotient_theorem"]
