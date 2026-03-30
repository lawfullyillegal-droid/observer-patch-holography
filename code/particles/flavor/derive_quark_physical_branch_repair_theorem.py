#!/usr/bin/env python3
"""Emit the honest D12 quark physical-branch no-go / repair theorem artifact.

Chain role: record the sharpest exact theorem the current D12 quark
continuation branch proves on the CKM side after transport closure is already
in hand.

Mathematics: the current D12 sheet has an honest forward same-label transport
unitary and principal logarithm, so CKM/CP transport closure is complete on
that sheet. But same-sheet rephasing changes only diagonal U(1)^3 phases, so
all CKM moduli and rephasing invariants are frozen. If those invariants are
wrong on the present sheet, no same-sheet repair can move them to the physical
shell. The minimal new object is therefore one discrete relative sheet
selector.

OPH-derived inputs: the current D12 mass/transport closure artifact.

Output: a theorem artifact stating that the present D12 sheet is a strict no-go
for the physical CKM shell, together with the exact next emitted object
``quark_relative_sheet_selector``.
"""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
D12_BRANCH_JSON = ROOT / "particles" / "runs" / "flavor" / "quark_d12_mass_branch_and_ckm_residual.json"
DEFAULT_OUT = ROOT / "particles" / "runs" / "flavor" / "quark_physical_branch_repair_theorem.json"

TARGET_THETA_12 = 0.2256
TARGET_THETA_23 = 0.0438
TARGET_THETA_13 = 0.00347


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _j_max(theta_12: float, theta_23: float, theta_13: float) -> float:
    s12 = math.sin(theta_12)
    s23 = math.sin(theta_23)
    s13 = math.sin(theta_13)
    c12 = math.cos(theta_12)
    c23 = math.cos(theta_23)
    c13 = math.cos(theta_13)
    return c12 * c23 * (c13**2) * s12 * s23 * s13


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the quark physical-branch repair theorem artifact.")
    parser.add_argument("--branch", default=str(D12_BRANCH_JSON))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    branch = _load_json(Path(args.branch))
    standard = dict(branch["standard_ckm_parameters"])

    theta_12 = float(standard["theta_12"])
    theta_23 = float(standard["theta_23"])
    theta_13 = float(standard["theta_13"])
    delta = float(standard["delta_ckm"])
    jarlskog = float(standard["jarlskog"])
    j_max = _j_max(theta_12, theta_23, theta_13)
    loss = (
        (theta_12 - TARGET_THETA_12) ** 2
        + (theta_23 - TARGET_THETA_23) ** 2
        + (theta_13 - TARGET_THETA_13) ** 2
    )

    artifact = {
        "artifact": "oph_quark_physical_branch_repair_theorem",
        "generated_utc": _timestamp(),
        "scope": "D12_continuation_only",
        "proof_status": "current_d12_sheet_is_strict_no_go_for_physical_ckm_shell",
        "public_promotion_allowed": False,
        "theorem_statement": (
            "Fix the current emitted ordered, nondegenerate up- and down-sector spectra together with the "
            "simple-spectrum D12 sheet. Every admissible same-sheet lift change is only "
            "U_u -> U_u P_u and U_d -> U_d P_d with P_u, P_d in diagonal U(1)^3, so "
            "V_CKM = U_u^dagger U_d changes only by left/right diagonal rephasing. Therefore all rephasing "
            "invariants |V_ij|, theta_12, theta_23, theta_13, and J are frozen on the current D12 sheet. "
            "Since the current sheet already has the wrong invariant magnitudes, no same-sheet rephase, local "
            "convention change, scalar rescaling, or compare-fit mass choice can move it to the physical CKM shell."
        ),
        "current_d12_sheet": {
            "branch_label": "D12",
            "branch_key": ["D12", None],
            "quark_relative_sheet_selector": None,
            "sheet_status": "single_local_reference_sheet_only",
            "local_solver_limit": "no_finite_relative_sheet_class_enumeration_exposed",
        },
        "insufficiency_theorem": {
            "id": "D12_relative_sheet_non_identifiability",
            "statement": (
                "From the presently emitted D12 quark-side data alone there is no sound function that can recover "
                "the finite set Sigma_ud, the selector sigma_ud, or the selected-branch CKM invariants. The current "
                "surface exposes only one evaluated reference-sheet representative, while same-sheet rephasing is "
                "already known to leave the CKM invariants frozen."
            ),
            "proof_obstruction": [
                "only one D12 reference-sheet representative is exposed",
                "Sigma_ud is not exposed as a finite enumerable set",
                "no relative-sheet evaluator sigma->CKM invariants is exposed",
                "same-sheet rephasing cannot change CKM invariants",
                "mass-side branch choice is excluded from CKM repair",
            ],
        },
        "comparison_shell": {
            "theta_12": TARGET_THETA_12,
            "theta_23": TARGET_THETA_23,
            "theta_13": TARGET_THETA_13,
            "source": "comparison_shell_debug_reference_only",
        },
        "current_sheet_invariants": {
            "theta_12": theta_12,
            "theta_23": theta_23,
            "theta_13": theta_13,
            "delta_ckm": delta,
            "jarlskog": jarlskog,
            "jarlskog_fraction_of_max_allowed_by_current_angles": (
                abs(jarlskog) / j_max if j_max > 0.0 else None
            ),
        },
        "physical_shell_mismatch": {
            "absolute_misses": {
                "theta_12": TARGET_THETA_12 - theta_12,
                "theta_23": TARGET_THETA_23 - theta_23,
                "theta_13": TARGET_THETA_13 - theta_13,
            },
            "undershoot_factors": {
                "theta_12": TARGET_THETA_12 / theta_12 if theta_12 > 0.0 else None,
                "theta_23": TARGET_THETA_23 / theta_23 if theta_23 > 0.0 else None,
                "theta_13": TARGET_THETA_13 / theta_13 if theta_13 > 0.0 else None,
            },
            "loss_function": (
                "(theta_12 - 0.2256)^2 + (theta_23 - 0.0438)^2 + (theta_13 - 0.00347)^2"
            ),
            "loss_value": loss,
        },
        "minimal_branch_shift_repair_theorem": {
            "id": "quark_relative_sheet_selector",
            "must_emit": "quark_relative_sheet_selector",
            "definition": "sigma_ud in Sigma_ud",
            "branch_key_after_repair": ["D12", "sigma_ud"],
            "must_not_use_compare_fit_masses": True,
            "must_not_use_same_sheet_rephasing": True,
            "selection_rule": {
                "loss_function": (
                    "(theta_12(sigma)-0.2256)^2 + (theta_23(sigma)-0.0438)^2 + "
                    "(theta_13(sigma)-0.00347)^2"
                ),
                "secondary_tiebreaker": "J(sigma)",
            },
        },
        "minimal_solver_extension": {
            "id": "sigma_ud_orbit",
            "definition": "full finite relative-sheet orbit over the present D12 reference representative",
            "must_emit": "sigma_ud_orbit.elements = [{sigma_id, canonical_token, ckm}]",
            "selection_rule_kind": "ckm_log_shell_loss",
            "selection_rule": {
                "loss_function": (
                    "sum_a [log(theta_a(sigma) / theta_a_star)]^2 for a in {12,23,13}"
                ),
                "shell": {
                    "theta_12": TARGET_THETA_12,
                    "theta_23": TARGET_THETA_23,
                    "theta_13": TARGET_THETA_13,
                },
                "tiebreak": [
                    "abs_log_error_theta13",
                    "abs_log_error_theta23",
                    "abs_log_error_theta12",
                    "canonical_sigma_id",
                ],
            },
        },
        "disqualified_existing_local_scan": {
            "status": "not_sigma_ud_orbit",
            "grid_kind": "np.linspace(-0.4, 0.4, 4001)",
            "scan_coordinate": "Delta_ud_overlap",
            "score": "RMS log error against reference_targets",
            "same_sheet_only": True,
            "uses_reference_targets": True,
            "why_disqualified": "The only finite scan currently exposed in local code is a same-sheet target-mass comparison scan over Delta_ud_overlap. It neither enumerates Sigma_ud nor emits a relative-sheet sigma->CKM evaluator, so it cannot honestly serve as branch repair.",
        },
        "relative_sheet_scan": {
            "status": "not_available_from_current_local_solver",
            "reason": (
                "The current local solver exposes only the evaluated D12 reference-sheet representative and does "
                "not expose a finite set Sigma_ud of relative sheet classes to enumerate."
            ),
            "selector_value": None,
        },
        "notes": [
            "This artifact sharpens the quark CKM boundary: the current D12 sheet is transport-closed but wrong-branch.",
            "The exact next object is discrete rather than continuous: one relative up/down sheet selector sigma_ud.",
            "The current surface is formally insufficient to identify sigma_ud; the minimal extension is a finite sigma_ud orbit with per-candidate CKM tuples.",
            "The only finite local scan on disk is a same-sheet Delta_ud_overlap scan against reference targets; it is comparison-only and cannot be repurposed as a Sigma_ud scan.",
            "Mass-side scale fixing remains a separate issue after the physical branch is selected; no scalar t1 can repair CKM on the present sheet.",
        ],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
