#!/usr/bin/env python3
"""Guard the residual-amplitude compare-only audit above the q_mean^p factorization."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_residual_amplitude_candidate_audit.py"
OUTPUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_residual_amplitude_candidate_audit.json"


def test_neutrino_residual_amplitude_candidate_audit() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(OUTPUT)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "saved:" in completed.stdout
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_neutrino_residual_amplitude_candidate_audit"
    assert payload["status"] == "compare_only_residual_amplitude_search"
    assert payload["public_promotion_allowed"] is False
    assert payload["residual_amplitude_definition"] == "A_nu = lambda_nu * q_mean^p_nu"
    target = payload["target_residual_ratio"]
    assert target["value"] > 1.0
    assert target["A_nu_star_eV"] > target["m_star_eV"]
    assert payload["selected_point_relative_phase_contract"]["definition"].startswith("delta_psi_e = psi_e")
    best = payload["best_compare_only_candidate"]
    assert best["complexity"] == 3
    assert best["formula"] == "I_nu^0.5 * ratio_hat^0.5 * sum_defect^-1"
    assert best["relative_error"] < 1.0e-3
    family_assisted = payload["best_family_assisted_compare_only_candidate"]
    assert any(key.endswith("_over_mstar") for key in family_assisted["keys"])
    assert family_assisted["relative_error"] < 1.0e-3
    assert payload["top_single_factor_candidates"][0]["complexity"] == 1
    assert payload["top_two_factor_candidates"][0]["complexity"] == 2
    assert payload["top_three_factor_candidates"][0]["complexity"] == 3
    assert payload["top_family_assisted_candidates"][0]["formula"] == family_assisted["formula"]
    assert "sqrt(I_nu) * sqrt(ratio_hat) / sum_defect" in payload["working_observation"]
