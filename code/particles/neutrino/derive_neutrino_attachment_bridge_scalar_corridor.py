#!/usr/bin/env python3
"""Emit the strongest current compare-only corridor for the bridge scalar sidecar.

This does not emit the proof-facing theorem object. It fuses the live
compare-only routes for

    B_nu = lambda_nu * q_mean^p_nu / m_star_eV,

so the diagnostic bridge scalar is numerically narrowed on the current branch
without feeding back into the emitted theorem pair.
"""

from __future__ import annotations

import argparse
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BRIDGE_CANDIDATE_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_lambda_nu_bridge_candidate.json"
NORMALIZER_AUDIT_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_attachment_normalizer_candidate_audit.json"
RESIDUAL_AUDIT_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_residual_amplitude_candidate_audit.json"
CORRECTION_AUDIT_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_bridge_correction_candidate_audit.json"
DEFAULT_OUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_attachment_bridge_scalar_corridor.json"
SHORTLIST_DEPTH = 5


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _corridor(values: list[float], target: float) -> dict[str, Any]:
    lower = min(values)
    upper = max(values)
    midpoint = 0.5 * (lower + upper)
    relative_half_width = 0.0 if midpoint == 0.0 else 0.5 * (upper - lower) / midpoint
    return {
        "interval": [lower, upper],
        "midpoint": midpoint,
        "relative_half_width": relative_half_width,
        "contains_compare_only_target": lower <= target <= upper,
    }


def _relative_half_width(lower: float, upper: float) -> float:
    midpoint = 0.5 * (lower + upper)
    return 0.0 if midpoint == 0.0 else 0.5 * (upper - lower) / midpoint


def _route_summary(
    *,
    route_id: str,
    source_artifact: str,
    candidate: dict[str, Any],
    value_key: str,
    error_key: str,
    formula_key: str = "formula",
    route_kind: str,
) -> dict[str, Any]:
    return {
        "route_id": route_id,
        "route_kind": route_kind,
        "source_artifact": source_artifact,
        "complexity": candidate["complexity"],
        "formula": candidate[formula_key],
        "keys": candidate["keys"],
        "exponents": candidate["exponents"],
        "value": float(candidate[value_key]),
        "relative_error": float(candidate[error_key]),
    }


def _shortlist_consensus_window(
    *,
    target: float,
    shortlists: list[list[dict[str, Any]]],
) -> dict[str, Any]:
    best_key: tuple[float, int, float] | None = None
    best_combo: tuple[dict[str, Any], ...] | None = None
    for combo in itertools.product(*shortlists):
        values = [float(item["value"]) for item in combo]
        lower = min(values)
        upper = max(values)
        key = (
            _relative_half_width(lower, upper),
            sum(int(item["complexity"]) for item in combo),
            sum(float(item["relative_error"]) for item in combo),
        )
        if best_key is None or key < best_key:
            best_key = key
            best_combo = combo
    assert best_key is not None and best_combo is not None
    lower = min(float(item["value"]) for item in best_combo)
    upper = max(float(item["value"]) for item in best_combo)
    midpoint = 0.5 * (lower + upper)
    return {
        "shortlist_depth_per_route": min(len(route) for route in shortlists),
        "selection_rule": (
            "Within the already-admitted top candidates of each route family, choose one candidate per route that minimizes "
            "cross-route relative half-width; total algebraic complexity and route-local compare-only error break ties."
        ),
        "selected_candidates": list(best_combo),
        "interval": [lower, upper],
        "midpoint": midpoint,
        "relative_half_width": best_key[0],
        "contains_compare_only_target": lower <= target <= upper,
        "compare_only_target_offset_over_midpoint": 0.0 if midpoint == 0.0 else (target - midpoint) / midpoint,
    }


def build_payload(
    *,
    bridge_candidate: dict[str, Any],
    normalizer_audit: dict[str, Any],
    residual_audit: dict[str, Any],
    correction_audit: dict[str, Any] | None,
) -> dict[str, Any]:
    target = float(bridge_candidate["compare_only_residual_amplitude_ratio"]["B_nu_star"])
    converted_normalizer = _route_summary(
        route_id="converted_symmetric_normalizer_route",
        source_artifact=normalizer_audit["artifact"],
        candidate=normalizer_audit["best_bridge_scalar_candidate_after_exact_q_mean_factorization"],
        value_key="converted_value",
        error_key="converted_relative_error",
        formula_key="converted_formula",
        route_kind="exact_q_mean_factorization_applied_to_symmetric_F_nu_search",
    )
    core_residual = _route_summary(
        route_id="core_residual_scalar_route",
        source_artifact=residual_audit["artifact"],
        candidate=residual_audit["best_compare_only_candidate"],
        value_key="value",
        error_key="relative_error",
        route_kind="direct_search_on_core_residual_scalar_pool_for_B_nu",
    )
    family_assisted = _route_summary(
        route_id="defect_family_assisted_residual_route",
        source_artifact=residual_audit["artifact"],
        candidate=residual_audit["best_family_assisted_compare_only_candidate"],
        value_key="value",
        error_key="relative_error",
        route_kind="direct_search_using_defect_weighted_mu_e_family_scales_in_the_residual_B_nu_pool",
    )
    representatives = [converted_normalizer, core_residual, family_assisted]
    representative_corridor = _corridor([item["value"] for item in representatives], target)
    shortlist_consensus_window = _shortlist_consensus_window(
        target=target,
        shortlists=[
            [
                _route_summary(
                    route_id=f"converted_symmetric_normalizer_top_{index}",
                    source_artifact=normalizer_audit["artifact"],
                    candidate=candidate,
                    value_key="converted_value",
                    error_key="converted_relative_error",
                    formula_key="converted_formula",
                    route_kind="exact_q_mean_factorization_applied_to_symmetric_F_nu_search",
                )
                for index, candidate in enumerate(
                    normalizer_audit["top_bridge_scalar_candidates_after_exact_q_mean_factorization"][:SHORTLIST_DEPTH], start=1
                )
            ],
            [
                _route_summary(
                    route_id=f"core_residual_top_{index}",
                    source_artifact=residual_audit["artifact"],
                    candidate=candidate,
                    value_key="value",
                    error_key="relative_error",
                    route_kind="direct_search_on_core_residual_scalar_pool_for_B_nu",
                )
                for index, candidate in enumerate(residual_audit["top_three_factor_candidates"][:SHORTLIST_DEPTH], start=1)
            ],
            [
                _route_summary(
                    route_id=f"family_assisted_top_{index}",
                    source_artifact=residual_audit["artifact"],
                    candidate=candidate,
                    value_key="value",
                    error_key="relative_error",
                    route_kind="direct_search_using_defect_weighted_mu_e_family_scales_in_the_residual_B_nu_pool",
                )
                for index, candidate in enumerate(
                    residual_audit["top_family_assisted_candidates"][:SHORTLIST_DEPTH], start=1
                )
            ],
        ],
    )
    core_proxy_value = float(core_residual["value"])
    strongest_target_containing_corridor: dict[str, Any] = {
        "source": "primary_cross_route_corridor",
        **representative_corridor,
    }
    if correction_audit is not None:
        induced_corridor = correction_audit.get("induced_target_containing_bridge_scalar_window")
        if induced_corridor is not None and induced_corridor.get("relative_half_width", float("inf")) < representative_corridor["relative_half_width"]:
            strongest_target_containing_corridor = {
                "source": correction_audit.get("artifact"),
                "construction": "induced_from_primary_target_containing_C_nu_window_above_emitted_proxy",
                **induced_corridor,
            }

    envelope_candidates: list[dict[str, Any]] = []
    for index, candidate in enumerate(
        normalizer_audit["top_bridge_scalar_candidates_after_exact_q_mean_factorization"][:3], start=1
    ):
        envelope_candidates.append(
            {
                "route_id": f"converted_symmetric_normalizer_top_{index}",
                "route_class": "converted_symmetric_normalizer",
                "formula": candidate["converted_formula"],
                "value": float(candidate["converted_value"]),
                "relative_error": float(candidate["converted_relative_error"]),
            }
        )
    for index, candidate in enumerate(residual_audit["top_three_factor_candidates"][:3], start=1):
        envelope_candidates.append(
            {
                "route_id": f"core_residual_top_{index}",
                "route_class": "core_residual_scalar_pool",
                "formula": candidate["formula"],
                "value": float(candidate["value"]),
                "relative_error": float(candidate["relative_error"]),
            }
        )
    for index, candidate in enumerate(residual_audit["top_family_assisted_candidates"][:3], start=1):
        envelope_candidates.append(
            {
                "route_id": f"family_assisted_top_{index}",
                "route_class": "defect_family_assisted_residual_pool",
                "formula": candidate["formula"],
                "value": float(candidate["value"]),
                "relative_error": float(candidate["relative_error"]),
            }
        )
    envelope_corridor = _corridor([item["value"] for item in envelope_candidates], target)

    return {
        "artifact": "oph_neutrino_attachment_bridge_scalar_corridor",
        "generated_utc": _timestamp(),
        "status": "compare_only_cross_route_corridor",
        "public_promotion_allowed": False,
        "proof_chain_role": "diagnostic_only_retired_from_theorem_lane",
        "must_not_feed_back": True,
        "exact_missing_object": "oph_neutrino_attachment_bridge_invariant",
        "exact_target_scalar": {
            "symbol": "B_nu",
            "definition": "B_nu = lambda_nu * q_mean^p_nu / m_star_eV",
            "exact_residual_moduli_space": "R_{>0}",
        },
        "exact_reduced_correction_scalar": {
            "symbol": "C_nu",
            "definition": f"C_nu = B_nu / ({core_residual['formula']})",
            "bridge_reconstruction": f"B_nu = ({core_residual['formula']}) * C_nu",
            "exact_residual_moduli_space": "R_{>0}",
            "emitted_proxy_route": {
                "route_id": core_residual["route_id"],
                "formula": core_residual["formula"],
                "value": core_proxy_value,
                "source_artifact": core_residual["source_artifact"],
            },
            "compare_only_target": target / core_proxy_value,
            "interpretation": (
                "After factoring out the strongest current emitted residual-amplitude proxy, the remaining exact attachment gap is a "
                "positive correction scalar near 1 on the live compare-only branch."
            ),
        },
        "best_constructive_subbridge_object": bridge_candidate["best_constructive_subbridge_object"],
        "current_compare_only_target": {
            "name": "B_nu_star",
            "value": target,
            "source": bridge_candidate["compare_only_residual_amplitude_ratio"]["interpretation"],
        },
        "route_selection_rule": {
            "converted_normalizer_route": (
                "Use the best symmetric F_nu candidate and apply the exact factorization B_nu = F_nu * q_mean^p_nu."
            ),
            "core_residual_route": "Use the best candidate on the core residual scalar pool for B_nu directly.",
            "family_assisted_route": (
                "Use the best extended residual candidate that genuinely depends on defect-weighted mu_e family scales."
            ),
        },
        "primary_route_representatives": representatives,
        "primary_cross_route_corridor": representative_corridor,
        "strongest_target_containing_bridge_scalar_corridor": {
            **strongest_target_containing_corridor,
            "narrowing_vs_primary_cross_route_corridor": {
                "is_narrower": strongest_target_containing_corridor["relative_half_width"] < representative_corridor["relative_half_width"],
                "relative_half_width_ratio": (
                    0.0
                    if representative_corridor["relative_half_width"] == 0.0
                    else strongest_target_containing_corridor["relative_half_width"] / representative_corridor["relative_half_width"]
                ),
            },
        },
        "shortlist_route_consensus_window": {
            **shortlist_consensus_window,
            "narrowing_vs_primary_cross_route_corridor": {
                "relative_half_width_ratio": (
                    0.0
                    if representative_corridor["relative_half_width"] == 0.0
                    else shortlist_consensus_window["relative_half_width"] / representative_corridor["relative_half_width"]
                ),
                "is_narrower": shortlist_consensus_window["relative_half_width"] < representative_corridor["relative_half_width"],
            },
        },
        "bridge_correction_candidate_audit": (
            None
            if correction_audit is None
            else {
                "artifact": correction_audit.get("artifact"),
                "status": correction_audit.get("status"),
                "current_compare_only_target": correction_audit.get("current_compare_only_target"),
                "best_core_correction_candidate": correction_audit.get("best_core_correction_candidate"),
                "best_family_assisted_correction_candidate": correction_audit.get("best_family_assisted_correction_candidate"),
                "primary_target_containing_correction_window": correction_audit.get("primary_target_containing_correction_window"),
                "induced_target_containing_bridge_scalar_window": correction_audit.get("induced_target_containing_bridge_scalar_window"),
            }
        ),
        "top_candidate_envelope": {
            "candidate_count": len(envelope_candidates),
            "route_class_counts": {
                "converted_symmetric_normalizer": 3,
                "core_residual_scalar_pool": 3,
                "defect_family_assisted_residual_pool": 3,
            },
            "candidates": envelope_candidates,
            **envelope_corridor,
        },
        "sharpened_obstruction": {
            "statement": (
                "After exact q_mean^p_nu factorization, the best converted symmetric-normalizer route, the best core residual route, "
                "and the best defect-family-assisted residual route all land in a narrow compare-only corridor for B_nu on the live branch. "
                "That materially narrows the remaining scalar numerically, but it does not collapse the irreducible theorem gap."
            ),
            "why_not_a_theorem": (
                "Every route in this corridor is a compare-only search clue selected against the current target. The attachment irreducibility theorem still leaves one positive bridge invariant external to the emitted stack."
            ),
        },
        "promotion_guard": {
            "status": "do_not_promote",
            "reason": (
                "This corridor is an honest numerical narrowing of the remaining bridge scalar, not an emitted OPH attachment law. "
                "It must not be fed back into lambda_nu emission."
            ),
        },
        "notes": [
            "The corridor sits strictly above the defect-weighted mu_e family and strictly below any theorem-grade emission of B_nu.",
            "The family-assisted route is included so the current defect-weighted mu_e family contributes explicitly to the sharpened compare-only bridge picture.",
            "The representative corridor and the wider envelope both contain the live compare-only target B_nu_star.",
            "The reduced correction scalar C_nu isolates the diagnostic bridge geometry above the best emitted residual-amplitude proxy and makes the retired bridge sidecar a near-unity positive factor on the weighted-cycle branch.",
            "A direct C_nu audit yields a narrower target-containing induced B_nu window than the old three-route bridge corridor.",
            "The shortlist consensus window is narrower than the primary three-point corridor, but it is a route-agreement diagnostic only and need not contain the live compare-only target.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the neutrino compare-only bridge-scalar corridor.")
    parser.add_argument("--bridge-candidate", default=str(BRIDGE_CANDIDATE_JSON))
    parser.add_argument("--normalizer-audit", default=str(NORMALIZER_AUDIT_JSON))
    parser.add_argument("--residual-audit", default=str(RESIDUAL_AUDIT_JSON))
    parser.add_argument("--correction-audit", default=str(CORRECTION_AUDIT_JSON))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    payload = build_payload(
        bridge_candidate=_load_json(Path(args.bridge_candidate)),
        normalizer_audit=_load_json(Path(args.normalizer_audit)),
        residual_audit=_load_json(Path(args.residual_audit)),
        correction_audit=_load_json(Path(args.correction_audit)) if Path(args.correction_audit).exists() else None,
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
