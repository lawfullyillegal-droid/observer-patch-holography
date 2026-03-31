#!/usr/bin/env python3
"""Guard the neutrino lambda_nu bridge candidate scaffold."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_lambda_nu_bridge_candidate.py"
OUTPUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_lambda_nu_bridge_candidate.json"


def test_neutrino_lambda_nu_bridge_candidate() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(OUTPUT)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "saved:" in completed.stdout
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_neutrino_lambda_nu_bridge_candidate"
    assert payload["current_candidate_interface_artifact"] == "oph_majorana_overlap_defect_scalar_evaluator"
    assert payload["closed_normalizer_artifact"] == "oph_same_label_overlap_defect_weight_normalizer"
    assert payload["exact_next_theorem_object"] == "oph_neutrino_attachment_bridge_invariant"
    assert payload["strictly_smaller_missing_clause"] is None
    assert payload["current_attached_stack_collapse_status"] == "refuted_by_attachment_irreducibility_theorem"
    assert payload["bridge_ansatz"] == "lambda_nu = (m_star_eV / q_mean^p_nu) * B_nu"
    assert payload["bridge_factor_schema"] == "B_nu = lambda_nu * q_mean^p_nu / m_star_eV"
    constructive = payload["best_constructive_subbridge_object"]
    assert constructive["artifact"] == "oph_defect_weighted_majorana_edge_weight_family"
    assert constructive["status"] == "closed_constructive_subbridge_object"
    assert constructive["raw_edge_score_rule"] == "q_e = sqrt(gap_e * defect_e)"
    assert constructive["mu_family_rule"] == "mu_e = mu_nu * exp(eta_e) / mean_f(exp(eta_f))"
    assert constructive["anisotropy_diagnostics"]["max_mu_over_min_mu"] > 2.0
    assert constructive["anisotropy_diagnostics"]["sigma_mu_over_mean_mu"] > 0.3
    residual = payload["residual_amplitude_parameterization"]
    assert residual["definition"] == "B_nu = lambda_nu * q_mean^p_nu / m_star_eV"
    assert residual["compare_only_B_nu_star"] > 1.0
    ruled_out = payload["ruled_out_current_selected_point_scalar"]
    assert ruled_out["status"] == "already_internal_to_current_emitted_stack_not_the_missing_bridge_scalar"
    assert ruled_out["selected_point"] == "weighted_cycle_selector_psi_wc"
    assert ruled_out["gate"] == "selector_overlap_phase_coboundary_trivializes_same_label_edge_transport"
    assert "0.5 * sum_e qbar_e" in ruled_out["definition"]
    stack = payload["bridge_interface_theorem_stack"]
    assert stack[0]["id"] == "oph_same_label_overlap_defect_weight_normalizer"
    assert stack[0]["status"] == "closed_from_live_same_label_scalar_certificate"
    assert stack[1]["id"] == "selector_overlap_phase_coboundary_trivializes_same_label_edge_transport"
    assert stack[1]["status"] == "closed_from_normalized_lift_coboundary"
    assert stack[2]["id"] == "selector_centered_unitary_common_refinement_descent_on_edge_bundle"
    assert stack[2]["status"] == "closed_from_normalized_common_refinement_unitary_transport"
    assert stack[3]["id"] == "oph_majorana_scalar_from_centered_edge_norm"
    assert stack[3]["status"] == "closed_on_current_isotropic_branch"
    assert stack[4]["id"] == "oph_neutrino_attachment_bridge_invariant"
    assert stack[5]["id"] == "neutrino_weighted_cycle_absolute_attachment"
    assert payload["compare_only_bridge_factor"]["F_nu_star"] > 1.0
    assert payload["compare_only_residual_amplitude_ratio"]["B_nu_star"] > 1.0
    assert payload["current_attached_stack_irreducibility_theorem"]["artifact"] == "oph_neutrino_attachment_irreducibility_theorem"
    closed_form = payload["target_free_closed_form_candidates"][0]
    assert closed_form["name"] == "gamma_over_sqrt_ratio_hat"
    assert closed_form["status"] == "exactly_refuted_as_theorem_grade_absolute_scale_law"
    assert closed_form["proof_obstruction"] == "positive_rescaling_nonidentifiability"
    assert abs(closed_form["residual_sigma"]["21"]) < 0.1
    assert abs(closed_form["residual_sigma"]["32"]) < 0.2
