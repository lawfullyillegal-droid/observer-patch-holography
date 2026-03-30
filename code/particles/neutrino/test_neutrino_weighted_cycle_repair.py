#!/usr/bin/env python3
"""Validate the repaired neutrino weighted-cycle branch artifact."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "particles" / "neutrino" / "derive_neutrino_weighted_cycle_repair.py"
CERTIFICATE = ROOT / "particles" / "runs" / "neutrino" / "same_label_scalar_certificate.json"
COCYCLE = ROOT / "particles" / "runs" / "flavor" / "overlap_edge_transport_cocycle.json"
PHASE_SOURCE = ROOT / "particles" / "runs" / "neutrino" / "intrinsic_neutrino_mass_eigenstate_bundle_from_scalar_certificate.json"
ISOTROPIC = ROOT / "particles" / "runs" / "neutrino" / "forward_neutrino_closure_bundle.json"


def test_repaired_weighted_cycle_branch_matches_expected_live_numbers() -> None:
    with tempfile.TemporaryDirectory(prefix="oph_neutrino_repair_") as tmpdir:
        out = pathlib.Path(tmpdir) / "repair.json"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--certificate",
                str(CERTIFICATE),
                "--cocycle",
                str(COCYCLE),
                "--phase-source",
                str(PHASE_SOURCE),
                "--isotropic",
                str(ISOTROPIC),
                "--output",
                str(out),
            ],
            check=True,
            cwd=ROOT,
        )
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["artifact"] == "oph_neutrino_weighted_cycle_repair"
        assert payload["final_verdict"] == "scale_free_physical_branch_closed_absolute_normalization_open"
        assert payload["theorem_status"] == "dimensionless_physical_branch_closed_absolute_normalization_open"
        assert payload["physical_window_status"] == "pmns_and_hierarchy_repaired"
        assert payload["symbolic_absolute_family"]["family_parameter"] == "lambda_nu > 0"
        assert payload["compare_only_atmospheric_anchor"]["adapter_status"] == "hard_separated_compare_only_adapter"
        assert abs(payload["weight_exponent"] - 1.406950210550122) < 1.0e-15
        assert abs(payload["diag_loading"] - 1.1045845502912137) < 1.0e-15
        assert abs(payload["pmns_observables"]["theta12_deg"] - 33.97561492020461) < 1.0e-10
        assert abs(payload["pmns_observables"]["theta23_deg"] - 49.77849428195363) < 1.0e-10
        assert abs(payload["pmns_observables"]["theta13_deg"] - 8.645937826302115) < 1.0e-10
        assert abs(payload["compare_only_atmospheric_anchor"]["delta_m32_sq_eV2"] - 2.433e-3) < 1.0e-15
        assert payload["pdg_2025_no_3sigma_window"]["within_window"]["theta12_deg"] is True
        assert payload["pdg_2025_no_3sigma_window"]["within_window"]["theta23_deg"] is True
        assert payload["pdg_2025_no_3sigma_window"]["within_window"]["theta13_deg"] is True
