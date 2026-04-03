#!/usr/bin/env python3
"""Validate the emitted neutrino bridge theorems."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
RIGIDITY_SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_bridge_rigidity_theorem.py"
ABSOLUTE_SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_absolute_attachment_theorem.py"
RIGIDITY_OUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_bridge_rigidity_theorem.json"
ABSOLUTE_OUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_absolute_attachment_theorem.json"


def test_neutrino_bridge_rigidity_and_absolute_attachment_are_emitted() -> None:
    for script in (RIGIDITY_SCRIPT, ABSOLUTE_SCRIPT):
        subprocess.run([sys.executable, str(script)], check=True, cwd=ROOT)

    rigidity = json.loads(RIGIDITY_OUT.read_text(encoding="utf-8"))
    absolute = json.loads(ABSOLUTE_OUT.read_text(encoding="utf-8"))

    assert rigidity["artifact"] == "oph_neutrino_bridge_rigidity_theorem"
    assert rigidity["status"] == "theorem_grade_emitted"
    assert rigidity["emitted_formula"] == "sum_gap^2 * prod_qbar * solar_response_over_mstar^-0.5"
    assert rigidity["emitted_value"] == pytest.approx(0.9994295999075177, abs=1.0e-15)

    assert absolute["artifact"] == "oph_neutrino_absolute_attachment_theorem"
    assert absolute["status"] == "theorem_grade_emitted"
    assert absolute["public_surface_candidate_allowed"] is True
    assert absolute["outputs"]["B_nu"] == pytest.approx(6.696004159297337, abs=1.0e-15)
    assert absolute["outputs"]["lambda_nu"] == pytest.approx(1.7237014208357415, abs=1.0e-15)
    assert absolute["outputs"]["masses_eV"][2] == pytest.approx(0.05307522145074924, abs=1.0e-15)
