#!/usr/bin/env python3
"""Validate the neutrino positive-scale-orbit audit artifact."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_absolute_scale_orbit_audit.py"
OUTPUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_absolute_scale_orbit_audit.json"


def test_neutrino_absolute_scale_orbit_audit_is_retired_beneath_emitted_theorem_pair() -> None:
    subprocess.run([sys.executable, str(SCRIPT)], check=True, cwd=ROOT)
    payload = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert payload["artifact"] == "oph_neutrino_absolute_scale_orbit_audit"
    assert payload["status"] == "diagnostic_only_retired_from_theorem_lane"
    assert payload["proof_chain_role"] == "diagnostic_only_retired_from_theorem_lane"
    assert payload["must_not_feed_back"] is True
    assert payload["no_hidden_discrete_branch"]["status"] == "closed"
    assert payload["no_hidden_discrete_branch"]["open_discrete_blockers"] == []
    assert payload["remaining_positive_scale_orbit"]["status"] == "closed_by_emitted_absolute_attachment_theorem"
    assert payload["remaining_positive_scale_orbit"]["group"] is None
    assert payload["remaining_object"] is None
