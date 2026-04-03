#!/usr/bin/env python3
"""Bundle the active theorem-grade neutrino lane into one closure artifact.

Chain role: collect the emitted weighted-cycle PMNS/hierarchy branch together
with the bridge-rigidity and absolute-attachment theorems into the forward
bundle used by audits and public-surface gating.

Mathematics: packaging only; this file does not derive new masses, but it keeps
the theorem tier, PMNS data, and emitted absolute family explicit.

OPH-derived inputs: the weighted-cycle theorem branch plus the emitted bridge
rigidity and absolute-attachment theorem artifacts.

Output: the forward neutrino closure bundle for downstream reporting.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WEIGHTED_CYCLE = ROOT / "particles" / "runs" / "neutrino" / "neutrino_weighted_cycle_repair.json"
DEFAULT_BRIDGE_RIGIDITY = ROOT / "particles" / "runs" / "neutrino" / "neutrino_bridge_rigidity_theorem.json"
DEFAULT_ABSOLUTE_ATTACHMENT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_absolute_attachment_theorem.json"
DEFAULT_OUT = ROOT / "particles" / "runs" / "neutrino" / "forward_neutrino_closure_bundle.json"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the forward neutrino closure-bundle artifact.")
    parser.add_argument("--weighted-cycle", default=str(DEFAULT_WEIGHTED_CYCLE))
    parser.add_argument("--bridge-rigidity", default=str(DEFAULT_BRIDGE_RIGIDITY))
    parser.add_argument("--absolute-attachment", default=str(DEFAULT_ABSOLUTE_ATTACHMENT))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    weighted_cycle = json.loads(Path(args.weighted_cycle).read_text(encoding="utf-8"))
    bridge_rigidity = json.loads(Path(args.bridge_rigidity).read_text(encoding="utf-8"))
    absolute_attachment = json.loads(Path(args.absolute_attachment).read_text(encoding="utf-8"))

    payload = {
        "artifact": "oph_forward_neutrino_closure_bundle",
        "generated_utc": _timestamp(),
        "closure_tier": "theorem_grade_emitted_weighted_cycle_absolute_family",
        "public_surface_candidate_allowed": True,
        "phase_mode": "weighted_cycle_bridge_rigid",
        "selector_law_certified": True,
        "certification_status": "theorem_grade_emitted",
        "weighted_cycle_branch": {
            "D_nu": weighted_cycle["selected_D_nu"],
            "p_nu": weighted_cycle.get("selected_p_nu", weighted_cycle["weight_exponent"]),
            "pmns_observables": weighted_cycle["pmns_observables"],
            "dimensionless_ratio_dm21_over_dm32": weighted_cycle["dimensionless_ratio_dm21_over_dm32"],
            "dimensionless_masses": weighted_cycle["dimensionless_masses"],
            "dimensionless_dm2": weighted_cycle["dimensionless_dm2"],
        },
        "bridge_rigidity": {
            "artifact": bridge_rigidity["artifact"],
            "C_nu": bridge_rigidity["emitted_value"],
            "P_nu": bridge_rigidity["emitted_proxy"]["value"],
            "formula": bridge_rigidity["emitted_formula"],
        },
        "absolute_attachment": absolute_attachment["outputs"],
        "masses_gev_sorted": [value * 1.0e-9 for value in absolute_attachment["outputs"]["masses_eV"]],
        "delta_m21_sq_gev2": absolute_attachment["outputs"]["delta_m_sq_eV2"]["21"] * 1.0e-18,
        "delta_m31_sq_gev2": absolute_attachment["outputs"]["delta_m_sq_eV2"]["31"] * 1.0e-18,
        "delta_m32_sq_gev2": absolute_attachment["outputs"]["delta_m_sq_eV2"]["32"] * 1.0e-18,
        "splitting_ratio_r": weighted_cycle["dimensionless_ratio_dm21_over_dm32"],
        "ordering_phase_certified": "normal_hierarchy_weighted_cycle_absolute_family",
        "pmns_status": "closed_on_weighted_cycle_branch",
        "notes": [
            "This bundle packages the emitted weighted-cycle bridge rigidity theorem together with the emitted absolute attachment theorem on one forward surface.",
            "The two-parameter exact adapter and the bridge corridor remain diagnostic-only sidecars beneath this theorem-grade bundle.",
            "The emitted absolute family is the proof-facing neutrino lane used by public status reporting.",
        ],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
