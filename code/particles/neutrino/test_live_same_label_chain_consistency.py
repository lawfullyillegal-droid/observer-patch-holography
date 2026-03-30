#!/usr/bin/env python3
"""Guard that the live same-label certificate chain matches its active builders."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFECT_SCRIPT = ROOT / "particles" / "neutrino" / "derive_defect_weighted_mu_e_family.py"
READBACK_SCRIPT = ROOT / "particles" / "neutrino" / "derive_realized_same_label_gap_defect_readback.py"
CERT_SCRIPT = ROOT / "particles" / "neutrino" / "derive_same_label_scalar_certificate.py"

SCALAR_EVALUATOR = ROOT / "particles" / "runs" / "neutrino" / "majorana_overlap_defect_scalar_evaluator.json"
FORWARD_BUNDLE = ROOT / "particles" / "runs" / "neutrino" / "forward_neutrino_closure_bundle.json"
FAMILY_KERNEL = ROOT / "particles" / "runs" / "flavor" / "family_transport_kernel.json"
LINE_LIFT = ROOT / "particles" / "runs" / "flavor" / "overlap_edge_line_lift.json"

LIVE_DEFECT = ROOT / "particles" / "runs" / "neutrino" / "defect_weighted_mu_e_family.json"
LIVE_READBACK = ROOT / "particles" / "runs" / "neutrino" / "realized_same_label_gap_defect_readback.json"
LIVE_CERT = ROOT / "particles" / "runs" / "neutrino" / "same_label_scalar_certificate.json"


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_live_same_label_chain_rebuilds_consistently() -> None:
    with tempfile.TemporaryDirectory(prefix="oph_live_same_label_chain_") as tmpdir:
        tmp = pathlib.Path(tmpdir)
        defect = tmp / "defect.json"
        readback = tmp / "readback.json"
        cert = tmp / "cert.json"

        subprocess.run(
            [
                sys.executable,
                str(DEFECT_SCRIPT),
                "--scalar",
                str(SCALAR_EVALUATOR),
                "--forward",
                str(FORWARD_BUNDLE),
                "--output",
                str(defect),
            ],
            check=True,
            cwd=ROOT,
        )
        subprocess.run(
            [
                sys.executable,
                str(READBACK_SCRIPT),
                "--input",
                str(defect),
                "--family-kernel",
                str(FAMILY_KERNEL),
                "--line-lift",
                str(LINE_LIFT),
                "--output",
                str(readback),
            ],
            check=True,
            cwd=ROOT,
        )
        subprocess.run(
            [
                sys.executable,
                str(CERT_SCRIPT),
                "--input",
                str(readback),
                "--output",
                str(cert),
            ],
            check=True,
            cwd=ROOT,
        )

        scalar_eval = _load(SCALAR_EVALUATOR)
        rebuilt_defect = _load(defect)
        rebuilt_readback = _load(readback)
        rebuilt_cert = _load(cert)
        live_defect = _load(LIVE_DEFECT)
        live_readback = _load(LIVE_READBACK)
        live_cert = _load(LIVE_CERT)

        expected_mu = float(scalar_eval["mu_nu"])
        for payload in (rebuilt_defect, rebuilt_readback, rebuilt_cert):
            assert float(payload["base_mu_nu"]) == pytest.approx(expected_mu, rel=0.0, abs=1.0e-18)
        assert float(live_defect["base_mu_nu"]) == pytest.approx(expected_mu, rel=0.0, abs=1.0e-18)
        assert float(live_readback["base_mu_nu"]) == pytest.approx(expected_mu, rel=0.0, abs=1.0e-18)
        assert float(live_cert["base_mu_nu"]) == pytest.approx(expected_mu, rel=0.0, abs=1.0e-18)

        assert live_readback["q_e"] == pytest.approx(rebuilt_readback["q_e"], rel=1.0e-12, abs=1.0e-15)
        assert live_cert["q_e"] == pytest.approx(rebuilt_cert["q_e"], rel=1.0e-12, abs=1.0e-15)
        assert live_cert["eta_e"] == pytest.approx(rebuilt_cert["eta_e"], rel=1.0e-12, abs=1.0e-15)
