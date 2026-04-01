#!/usr/bin/env python3
"""Emit the no-hidden-discrete-branch / positive-scale-orbit neutrino audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPAIR_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_weighted_cycle_repair.json"
BLOCKERS_JSON = ROOT / "particles" / "runs" / "neutrino" / "exact_blocking_items.json"
CERTIFICATE_JSON = ROOT / "particles" / "runs" / "neutrino" / "same_label_scalar_certificate.json"
DEFAULT_OUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_absolute_scale_orbit_audit.json"
THEOREM_NAME = "repaired_weighted_cycle_no_hidden_discrete_branch_and_positive_scale_orbit"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build_audit(repair: dict[str, Any], blockers: dict[str, Any], certificate: dict[str, Any] | None = None) -> dict[str, Any]:
    _require(repair.get("artifact") == "oph_neutrino_weighted_cycle_repair", "repair artifact mismatch")
    _require(repair.get("physical_window_status") == "pmns_and_hierarchy_repaired", "repair lane is not dimensionlessly physical")
    _require(repair.get("absolute_normalization_status") == "open_one_positive_scale", "absolute normalization is not the expected open state")
    _require(repair.get("cycle_basis_order") == ["f3", "f1", "f2"], "cycle basis order is not fixed to the live branch")
    _require(repair.get("holonomy_orientation") == "021", "holonomy orientation is not fixed to the live branch")

    closed_chain = list(blockers.get("closed_theorem_chain") or [])
    _require("shape_closed_scale_invariant_left_basis" in closed_chain, "missing shape_closed_scale_invariant_left_basis")
    _require("pmns_from_shared_charged_and_intrinsic_bases" in closed_chain, "missing pmns_from_shared_charged_and_intrinsic_bases")

    exact_blockers = list(blockers.get("exact_blockers") or [])
    _require(len(exact_blockers) == 1, f"expected exactly one open exact blocker, got {len(exact_blockers)}")
    only = exact_blockers[0]
    _require(only.get("name") == "one_positive_neutrino_bridge_correction_invariant", "wrong remaining blocker name")
    _require(only.get("kind") == "reduced_bridge_correction_invariant", "wrong remaining blocker kind")

    live = dict(blockers.get("live_continuation_branch_status") or {})
    no_go = dict(live.get("absolute_scale_no_go") or {})
    _require(no_go.get("theorem") == "neutrino_weighted_cycle_absolute_scale_no_go", "wrong no-go theorem name")
    _require(no_go.get("proof_obstruction") == "positive_rescaling_nonidentifiability", "wrong obstruction")

    compare_only = dict(live.get("compare_only_atmospheric_anchor") or {})
    _require(compare_only.get("status") == "compare_only", "compare-only anchor status mismatch")

    certificate_summary: dict[str, Any] = {}
    if certificate is not None:
        _require(certificate.get("artifact") == "oph_neutrino_same_label_scalar_certificate", "certificate artifact mismatch")
        certificate_summary = {
            "artifact": certificate.get("artifact"),
            "proof_status": certificate.get("proof_status"),
            "exact_downstream_factorization_object": certificate.get("exact_downstream_factorization_object"),
            "builder_facing_exact_object": certificate.get("builder_facing_exact_object"),
            "smallest_constructive_missing_object": certificate.get("smallest_constructive_missing_object"),
        }

    return {
        "artifact": "oph_neutrino_absolute_scale_orbit_audit",
        "generated_utc": _timestamp(),
        "status": "closed",
        "theorem": THEOREM_NAME,
        "theorem_statement": (
            "On the current repaired weighted-cycle neutrino lane, no unresolved discrete branch remains, and the exact remaining "
            "theorem object is the reduced bridge-correction invariant C_nu above the emitted proxy P_nu. Equivalently, the branch "
            "still carries one positive absolute-rescaling orbit lambda_nu -> s * lambda_nu with s > 0."
        ),
        "proof_primitives": {
            "repair_artifact": {
                "artifact": repair.get("artifact"),
                "cycle_basis_order": repair.get("cycle_basis_order"),
                "holonomy_orientation": repair.get("holonomy_orientation"),
                "physical_window_status": repair.get("physical_window_status"),
                "absolute_normalization_status": repair.get("absolute_normalization_status"),
                "symbolic_absolute_family": repair.get("symbolic_absolute_family"),
            },
            "blocker_audit": {
                "artifact": blockers.get("artifact"),
                "closed_theorem_chain": closed_chain,
                "exact_blockers": exact_blockers,
                "absolute_scale_no_go": no_go,
                "compare_only_atmospheric_anchor": compare_only,
            },
            "same_label_scalar_certificate": certificate_summary,
        },
        "no_hidden_discrete_branch": {
            "status": "closed",
            "open_discrete_blockers": [],
            "closed_discrete_witnesses": [
                "shape_closed_scale_invariant_left_basis",
                "pmns_from_shared_charged_and_intrinsic_bases",
                "cycle_basis_order_fixed_(f3,f1,f2)",
                "holonomy_orientation_fixed_021",
            ],
            "statement": "The live branch already fixes the shared-basis discrete data and the blocker surface carries no unresolved discrete theorem object.",
        },
        "remaining_positive_scale_orbit": {
            "status": "open",
            "group": "R_{>0}",
            "family_parameter": "lambda_nu > 0",
            "action_on_lambda_nu": "lambda_nu -> s * lambda_nu, s > 0",
            "action_on_masses": "m_i -> s * m_i",
            "action_on_splittings": "Delta m^2_ij -> s^2 * Delta m^2_ij",
            "scale_free_mass_normal_form": no_go.get("scale_free_mass_normal_form") or repair.get("scale_free_mass_normal_form"),
            "scale_free_dm2_normal_form_eV2": no_go.get("scale_free_dm2_normal_form_eV2"),
            "proof_obstruction": no_go.get("proof_obstruction"),
        },
        "remaining_object": only.get("name"),
        "remaining_object_kind": only.get("kind"),
        "remaining_object_contract": only.get("required_contract"),
        "next_breaking_contract": no_go.get("minimal_missing_object"),
        "compare_only_anchor_separation": {
            "external_anchor_disallowed": no_go.get("external_anchor_disallowed"),
            "hard_separated_compare_only_adapter": no_go.get("hard_separated_compare_only_adapter"),
            "current_compare_only_anchor": compare_only,
        },
        "solver_output_contract": {
            "emit_now": [
                "scale_free_mass_normal_form_mhat",
                "scale_free_dm2_normal_form_Delta_hat",
                "dimensionless_ratio_Delta21_over_Delta32",
                "pmns_observables",
                "no_hidden_discrete_branch_closed",
                "remaining_positive_scale_orbit_open",
            ],
            "must_not_emit_without_new_theorem": [
                "lambda_nu",
                "absolute_neutrino_masses",
                "absolute_delta_m2_values",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the neutrino positive-scale orbit audit.")
    parser.add_argument("--repair", default=str(REPAIR_JSON))
    parser.add_argument("--blockers", default=str(BLOCKERS_JSON))
    parser.add_argument("--certificate", default=str(CERTIFICATE_JSON))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    repair = _load_json(Path(args.repair))
    blockers = _load_json(Path(args.blockers))
    certificate = _load_json(Path(args.certificate)) if args.certificate else None
    audit = build_audit(repair, blockers, certificate)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
