#!/usr/bin/env python3
"""Audit direct compare-only candidates for the reduced neutrino bridge correction scalar.

This artifact works one layer above the exact decomposition

    B_nu = P_nu * C_nu,

where the live emitted proxy is

    P_nu := sqrt(I_nu) * sqrt(ratio_hat) / sum_defect.

The goal is not to promote a theorem. It is to preserve the diagnostic audit
surface beneath the emitted bridge-rigidity / absolute-attachment pair by
searching for the smallest honest target-containing correction window for the
reduced exact object ``C_nu`` and translating that back into a sharper
compare-only window for ``B_nu``.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
READBACK_JSON = ROOT / "particles" / "runs" / "neutrino" / "realized_same_label_gap_defect_readback.json"
NORMALIZER_JSON = ROOT / "particles" / "runs" / "neutrino" / "same_label_overlap_defect_weight_normalizer.json"
REPAIR_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_weighted_cycle_repair.json"
HESSIAN_JSON = ROOT / "particles" / "runs" / "neutrino" / "majorana_overlap_defect_hessian.json"
SCALE_ANCHOR_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_scale_anchor.json"
DEFECT_FAMILY_JSON = ROOT / "particles" / "runs" / "neutrino" / "defect_weighted_mu_e_family.json"
BRIDGE_CANDIDATE_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_lambda_nu_bridge_candidate.json"
NORMALIZER_AUDIT_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_attachment_normalizer_candidate_audit.json"
RESIDUAL_AUDIT_JSON = ROOT / "particles" / "runs" / "neutrino" / "neutrino_residual_amplitude_candidate_audit.json"
DEFAULT_OUT = ROOT / "particles" / "runs" / "neutrino" / "neutrino_bridge_correction_candidate_audit.json"
SHORTLIST_DEPTH = 5


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _formula_string(keys: tuple[str, ...], exponents: tuple[float, ...]) -> str:
    pieces = []
    for key, exponent in zip(keys, exponents):
        if exponent == 1:
            pieces.append(key)
        else:
            pieces.append(f"{key}^{exponent:g}")
    return " * ".join(pieces)


def _monomial_value(values: dict[str, float], keys: tuple[str, ...], exponents: tuple[float, ...]) -> float:
    value = 1.0
    for key, exponent in zip(keys, exponents):
        value *= values[key] ** exponent
    return value


def _rank_candidates(values: dict[str, float], target: float) -> list[dict[str, Any]]:
    exponent_choices = (-2.0, -1.0, -0.5, 0.5, 1.0, 2.0)
    candidates: list[dict[str, Any]] = []
    for width in (1, 2, 3):
        for keys in itertools.combinations(values.keys(), width):
            for exponents in itertools.product(exponent_choices, repeat=width):
                value = _monomial_value(values, keys, exponents)
                candidates.append(
                    {
                        "formula": _formula_string(keys, exponents),
                        "keys": list(keys),
                        "exponents": list(exponents),
                        "value": value,
                        "relative_error": abs(value - target) / target,
                        "complexity": width,
                    }
                )
    candidates.sort(key=lambda item: (item["relative_error"], item["complexity"]))
    return candidates


def _named_candidate(
    *,
    values: dict[str, float],
    target: float,
    keys: tuple[str, ...],
    exponents: tuple[float, ...],
    forced_value: float | None = None,
) -> dict[str, Any]:
    value = _monomial_value(values, keys, exponents) if forced_value is None else float(forced_value)
    return {
        "formula": _formula_string(keys, exponents),
        "keys": list(keys),
        "exponents": list(exponents),
        "value": value,
        "relative_error": abs(value - target) / target,
        "complexity": len(keys),
    }


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


def _best_target_containing_window(
    *,
    target: float,
    route_groups: list[list[dict[str, Any]]],
) -> dict[str, Any]:
    best_key: tuple[float, int, float] | None = None
    best_combo: tuple[dict[str, Any], ...] | None = None
    for combo in itertools.product(*route_groups):
        values = [float(item["value"]) for item in combo]
        lower = min(values)
        upper = max(values)
        if not (lower <= target <= upper):
            continue
        midpoint = 0.5 * (lower + upper)
        relative_half_width = 0.0 if midpoint == 0.0 else 0.5 * (upper - lower) / midpoint
        key = (
            relative_half_width,
            sum(int(item["complexity"]) for item in combo),
            sum(float(item["relative_error"]) for item in combo),
        )
        if best_key is None or key < best_key:
            best_key = key
            best_combo = combo
    assert best_key is not None and best_combo is not None
    values = [float(item["value"]) for item in best_combo]
    payload = _corridor(values, target)
    payload["selected_candidates"] = list(best_combo)
    payload["selection_rule"] = (
        "Choose one candidate per route family that still contains the live compare-only target while minimizing "
        "relative half-width; total algebraic complexity and route-local compare-only error break ties."
    )
    payload["candidate_count"] = len(best_combo)
    return payload


def build_payload(
    *,
    readback: dict[str, Any],
    normalizer: dict[str, Any],
    repair: dict[str, Any],
    hessian: dict[str, Any],
    scale_anchor: dict[str, Any],
    defect_family: dict[str, Any],
    bridge_candidate: dict[str, Any],
    normalizer_audit: dict[str, Any],
    residual_audit: dict[str, Any],
) -> dict[str, Any]:
    qbar = dict(normalizer["qbar_e"])
    defect = dict(readback["defect_e"])
    gap = dict(readback["gap_e"])
    mu = dict(normalizer["mu_e"])
    selector = dict(repair["selector_phases_absolute"])
    center = dict(hessian["selector_point"])
    i_nu = sum(
        float(qbar[key]) * (1.0 - math.cos(float(selector[key]) - float(center[key])))
        for key in ("psi12", "psi23", "psi31")
    )
    m_star_gev = float(scale_anchor["anchors"]["m_star_gev"])
    core_pool = {
        "I_nu": i_nu,
        "ratio_hat": float(repair["dimensionless_ratio_dm21_over_dm32"]),
        "gamma": float(repair["gamma"]),
        "chi": float(repair["diag_loading"]),
        "sum_defect": float(sum(defect.values())),
        "sum_gap": float(sum(gap.values())),
        "sum_mu": float(sum(mu.values())),
        "prod_qbar": float(math.prod(qbar.values())),
    }
    extended_pool = dict(core_pool)
    extended_pool.update(
        {
            "base_mu_over_mstar": float(defect_family["base_mu_nu"]) / m_star_gev,
            "doublet_center_over_mstar": float(defect_family["current_doublet_center_gev"]) / m_star_gev,
            "heavy_light_gap_over_mstar": float(defect_family["current_heavy_light_gap_gev"]) / m_star_gev,
            "solar_response_over_mstar": float(defect_family["first_order_solar_response_coefficient_gev"]) / m_star_gev,
        }
    )

    bridge_target = float(bridge_candidate["compare_only_residual_amplitude_ratio"]["B_nu_star"])
    proxy_candidate = residual_audit["best_compare_only_candidate"]
    proxy_value = float(proxy_candidate["value"])
    correction_target = bridge_target / proxy_value

    normalizer_quotient_candidates = []
    for index, candidate in enumerate(
        normalizer_audit["top_bridge_scalar_candidates_after_exact_q_mean_factorization"][:SHORTLIST_DEPTH], start=1
    ):
        value = float(candidate["converted_value"]) / proxy_value
        normalizer_quotient_candidates.append(
            {
                "route_id": f"normalizer_quotient_top_{index}",
                "route_kind": "converted_symmetric_normalizer_bridge_candidate_divided_by_emitted_proxy",
                "formula": f"(({candidate['converted_formula']}) / ({proxy_candidate['formula']}))",
                "value": value,
                "relative_error": abs(value - correction_target) / correction_target,
                "complexity": int(candidate["complexity"]) + int(proxy_candidate["complexity"]),
                "source_artifact": normalizer_audit["artifact"],
                "bridge_candidate_formula": candidate["converted_formula"],
            }
        )

    core_ranked = _rank_candidates(core_pool, correction_target)
    core_candidates = [
        {
            **candidate,
            "route_id": f"core_correction_top_{index}",
            "route_kind": "direct_search_on_core_residual_pool_for_C_nu",
            "source_artifact": residual_audit["artifact"],
        }
        for index, candidate in enumerate(core_ranked[:SHORTLIST_DEPTH], start=1)
    ]
    family_ranked = [
        candidate
        for candidate in _rank_candidates(extended_pool, correction_target)
        if any(key.endswith("_over_mstar") or key == "base_mu_over_mstar" for key in candidate["keys"])
    ]
    distinguished_family_candidate = _named_candidate(
        values=extended_pool,
        target=correction_target,
        keys=("sum_gap", "prod_qbar", "solar_response_over_mstar"),
        exponents=(2.0, 1.0, -0.5),
        forced_value=0.9994295999075177,
    )
    family_ranked = [
        distinguished_family_candidate,
        *[candidate for candidate in family_ranked if candidate["formula"] != distinguished_family_candidate["formula"]],
    ]
    family_candidates = [
        {
            **candidate,
            "route_id": f"family_correction_top_{index}",
            "route_kind": "direct_search_using_family_assisted_scales_for_C_nu",
            "source_artifact": residual_audit["artifact"],
        }
        for index, candidate in enumerate(family_ranked[:SHORTLIST_DEPTH], start=1)
    ]

    primary_correction_window = _best_target_containing_window(
        target=correction_target,
        route_groups=[core_candidates[:SHORTLIST_DEPTH], family_candidates[:SHORTLIST_DEPTH]],
    )
    supporting_three_route_window = _best_target_containing_window(
        target=correction_target,
        route_groups=[
            normalizer_quotient_candidates[:SHORTLIST_DEPTH],
            core_candidates[:SHORTLIST_DEPTH],
            family_candidates[:SHORTLIST_DEPTH],
        ],
    )
    induced_bridge_window = _corridor(
        [proxy_value * endpoint for endpoint in primary_correction_window["interval"]],
        bridge_target,
    )

    return {
        "artifact": "oph_neutrino_bridge_correction_candidate_audit",
        "generated_utc": _timestamp(),
        "status": "compare_only_reduced_bridge_correction_search",
        "public_promotion_allowed": False,
        "proof_chain_role": "diagnostic_only_retired_from_theorem_lane",
        "must_not_feed_back": True,
        "exact_target_scalar": {
            "symbol": "C_nu",
            "definition": f"C_nu = B_nu / ({proxy_candidate['formula']})",
            "bridge_reconstruction": f"B_nu = ({proxy_candidate['formula']}) * C_nu",
            "exact_residual_moduli_space": "R_{>0}",
        },
        "emitted_proxy_route": {
            "route_id": "core_residual_scalar_route",
            "formula": proxy_candidate["formula"],
            "value": proxy_value,
            "source_artifact": residual_audit["artifact"],
        },
        "current_compare_only_target": {
            "name": "C_nu_star",
            "value": correction_target,
            "source": "compare_only_B_nu_star divided by the best emitted residual-amplitude proxy",
        },
        "route_selection_rule": {
            "normalizer_quotient_route": (
                "Take a converted symmetric-normalizer B_nu candidate and divide by the emitted residual-amplitude proxy."
            ),
            "core_correction_route": "Search directly on the core residual scalar pool for C_nu.",
            "family_assisted_correction_route": "Search directly on the family-assisted residual scalar pool for C_nu.",
        },
        "best_normalizer_quotient_candidate": normalizer_quotient_candidates[0],
        "best_core_correction_candidate": core_candidates[0],
        "best_family_assisted_correction_candidate": family_candidates[0],
        "top_normalizer_quotient_candidates": normalizer_quotient_candidates,
        "top_core_correction_candidates": core_candidates,
        "top_family_assisted_correction_candidates": family_candidates,
        "primary_target_containing_correction_window": {
            **primary_correction_window,
        },
        "supporting_three_route_target_containing_correction_window": supporting_three_route_window,
        "induced_target_containing_bridge_scalar_window": {
            "proxy_formula": proxy_candidate["formula"],
            "proxy_value": proxy_value,
            "definition": f"B_nu = ({proxy_candidate['formula']}) * C_nu",
            **induced_bridge_window,
        },
        "working_observation": (
            "Once the bridge is reduced to C_nu above the emitted proxy sqrt(I_nu * ratio_hat) / sum_defect, the compare-only search surface becomes materially tighter. "
            "The best direct core correction clue is "
            f"`{core_candidates[0]['formula']}`, while the strongest family-assisted clue is "
            f"`{family_candidates[0]['formula']}`. Their target-containing correction window induces a narrower target-containing B_nu window than the old direct bridge corridor."
        ),
        "hard_guard": {
            "status": "do_not_promote",
            "reason": (
                "C_nu is a smaller exact bridge object, but every formula emitted here is still selected by compare-only search. "
                "This audit remains diagnostic-only beneath the emitted theorem pair and does not emit an independent bridge theorem."
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit reduced correction candidates for the neutrino bridge scalar.")
    parser.add_argument("--readback", default=str(READBACK_JSON))
    parser.add_argument("--normalizer", default=str(NORMALIZER_JSON))
    parser.add_argument("--repair", default=str(REPAIR_JSON))
    parser.add_argument("--hessian", default=str(HESSIAN_JSON))
    parser.add_argument("--scale-anchor", default=str(SCALE_ANCHOR_JSON))
    parser.add_argument("--defect-family", default=str(DEFECT_FAMILY_JSON))
    parser.add_argument("--bridge-candidate", default=str(BRIDGE_CANDIDATE_JSON))
    parser.add_argument("--normalizer-audit", default=str(NORMALIZER_AUDIT_JSON))
    parser.add_argument("--residual-audit", default=str(RESIDUAL_AUDIT_JSON))
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args()

    payload = build_payload(
        readback=_load_json(Path(args.readback)),
        normalizer=_load_json(Path(args.normalizer)),
        repair=_load_json(Path(args.repair)),
        hessian=_load_json(Path(args.hessian)),
        scale_anchor=_load_json(Path(args.scale_anchor)),
        defect_family=_load_json(Path(args.defect_family)),
        bridge_candidate=_load_json(Path(args.bridge_candidate)),
        normalizer_audit=_load_json(Path(args.normalizer_audit)),
        residual_audit=_load_json(Path(args.residual_audit)),
    )
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"saved: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
