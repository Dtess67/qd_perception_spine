"""
Family Stability / Split-Pressure Forecast v1.

Diagnostic only:
- no event creation
- no lineage mutation
- no probability claims
"""

from typing import Any


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _normalize(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.0
    return _clamp01((value - low) / (high - low))


def evaluate_family_pressure_forecast(*, family_id: str, signals: dict[str, Any], thresholds: dict[str, Any]) -> dict:
    """
    Evaluates neutral pressure state from pre-computed structural signals.
    Scorecard values are comparative diagnostics on [0, 1], not probabilities.
    """
    warnings: list[str] = []
    explanation_lines: list[str] = []

    evidence_sufficient = bool(signals.get("evidence_sufficient", False))
    if not evidence_sufficient:
        warnings.extend(list(signals.get("evidence_warnings", [])))
        explanation_lines.append("Evidence is insufficient or incomplete; returning hold posture.")
        return {
            "family_id": family_id,
            "pressure_state": "PRESSURE_UNCLEAR",
            "scorecard": {
                "diagnostic_scale": "0_to_1_comparative_not_probability",
                "stability_index": 0.0,
                "stretch_pressure_index": 0.0,
                "dual_center_pressure_index": 0.0,
                "instability_pressure_index": 0.0,
                "boundary_tension_index": 0.0,
                "fission_pressure_index": 0.0,
            },
            "signals": signals,
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
        }

    shape_class = str(signals.get("shape_class", "SHAPE_UNKNOWN"))
    compression_risk = bool(signals.get("compression_risk", False))
    anisotropy_ratio = float(signals.get("anisotropy_ratio", 0.0))
    pairwise_ratio = float(signals.get("pairwise_distance_ratio", 0.0))
    subgroup_count = int(signals.get("subgroup_count", 1))
    subgroup_evidence_counter = int(signals.get("subgroup_evidence_counter", 0))
    fracture_status = signals.get("fracture_status")
    fracture_counter = int(signals.get("fracture_counter", 0))
    fission_candidate_counter = int(signals.get("fission_candidate_counter", 0))
    bridge_fraction = float(signals.get("bridge_fraction", 0.0))
    edge_fraction = float(signals.get("edge_fraction", 0.0))
    geometry_fit_status = str(signals.get("geometry_fit_status", "GEOMETRY_FIT_UNKNOWN"))
    recent_transition_count = int(signals.get("recent_transition_count", 0))

    subgroup_persist_ratio = _normalize(
        float(subgroup_evidence_counter),
        0.0,
        float(max(1, int(thresholds["subgroup_persistence_threshold"]))),
    )
    fracture_persist_ratio = _normalize(
        float(fracture_counter),
        0.0,
        float(max(1, int(thresholds["fracture_persistence_threshold"]))),
    )
    fission_candidate_ratio = _normalize(
        float(fission_candidate_counter),
        0.0,
        float(max(1, int(thresholds["fission_persistence_threshold"]))),
    )

    axis_term = _normalize(
        anisotropy_ratio,
        float(thresholds["topology_compact_anisotropy_max"]),
        float(thresholds["topology_elongated_anisotropy_min"]),
    )
    pair_term = _normalize(
        pairwise_ratio,
        float(thresholds["topology_compact_pairwise_ratio_max"]),
        float(thresholds["topology_elongated_pairwise_ratio_min"]),
    )

    stretch_pressure = max(axis_term, pair_term)
    if shape_class == "SHAPE_ELONGATED":
        stretch_pressure += 0.25
    if compression_risk and shape_class != "SHAPE_DUAL_LOBE":
        stretch_pressure += 0.10
    stretch_pressure += (0.15 * edge_fraction) + (0.15 * bridge_fraction)
    stretch_pressure = _clamp01(stretch_pressure)

    dual_center_pressure = 0.0
    if shape_class == "SHAPE_DUAL_LOBE":
        dual_center_pressure += 0.65
    elif shape_class == "SHAPE_ELONGATED":
        dual_center_pressure += 0.15
    elif shape_class == "SHAPE_COMPACT":
        dual_center_pressure += 0.05
    else:
        dual_center_pressure += 0.20
    if compression_risk:
        dual_center_pressure += 0.20
    if subgroup_count >= 2:
        dual_center_pressure += 0.20
    dual_center_pressure += (0.25 * subgroup_persist_ratio)
    dual_center_pressure = _clamp01(dual_center_pressure)

    instability_pressure = 0.10
    if fracture_status == "FAMILY_FRACTURE_HOLD":
        instability_pressure = 0.35
    if fracture_status == "FAMILY_SPLIT_READY":
        instability_pressure = 0.65
    instability_pressure += (0.20 * fracture_persist_ratio)
    instability_pressure += (0.20 * fission_candidate_ratio)
    instability_pressure += (0.10 * bridge_fraction)
    if geometry_fit_status == "FIT_RESIDUAL_HIGH":
        instability_pressure += 0.15
    elif geometry_fit_status == "FAMILY_GEOMETRY_FIT_DECAY":
        instability_pressure += 0.08
    if recent_transition_count > 0:
        instability_pressure += 0.05
    instability_pressure = _clamp01(instability_pressure)

    boundary_tension = _clamp01((0.7 * bridge_fraction) + (0.5 * edge_fraction))
    fission_pressure = _clamp01(
        (0.45 * dual_center_pressure)
        + (0.35 * instability_pressure)
        + (0.15 * stretch_pressure)
        + (0.05 * boundary_tension)
    )
    stability_index = _clamp01(1.0 - max(stretch_pressure, dual_center_pressure, instability_pressure, fission_pressure))

    contradiction = False
    if shape_class == "SHAPE_COMPACT" and subgroup_count >= 2:
        contradiction = True
        warnings.append("PRESSURE_SIGNAL_CONTRADICTION")
        explanation_lines.append("Compact shape class conflicts with persistent subgroup count.")

    state = "PRESSURE_UNCLEAR"
    if (
        fission_pressure >= float(thresholds["pressure_fission_prone_threshold"])
        and dual_center_pressure >= float(thresholds["pressure_dual_center_threshold"])
        and instability_pressure >= float(thresholds["pressure_instability_threshold"])
    ):
        state = "PRESSURE_FISSION_PRONE"
    elif dual_center_pressure >= float(thresholds["pressure_dual_center_threshold"]):
        state = "PRESSURE_DUAL_CENTER_RISK"
    elif stretch_pressure >= float(thresholds["pressure_stretched_threshold"]):
        state = "PRESSURE_STRETCHED"
    elif (
        stability_index >= float(thresholds["pressure_stable_threshold"])
        and max(stretch_pressure, dual_center_pressure, instability_pressure) < float(thresholds["pressure_stretched_threshold"])
    ):
        state = "PRESSURE_STABLE"
    else:
        state = "PRESSURE_UNCLEAR"

    if contradiction and state == "PRESSURE_STABLE":
        state = "PRESSURE_UNCLEAR"

    if state == "PRESSURE_STABLE":
        explanation_lines.append("Topology and subgroup signals are low; structural pressure remains stable.")
    if state == "PRESSURE_STRETCHED":
        explanation_lines.append("Elongation pressure is elevated without strong dual-center evidence.")
    if state == "PRESSURE_DUAL_CENTER_RISK":
        explanation_lines.append("Topology/subgroup signals indicate elevated dual-center risk.")
    if state == "PRESSURE_FISSION_PRONE":
        explanation_lines.append("Dual-center and instability pressure are jointly elevated.")
    if state == "PRESSURE_UNCLEAR":
        explanation_lines.append("Signals are mixed or below confidence thresholds; hold posture is applied.")

    if compression_risk:
        warnings.append("TOPOLOGY_COMPRESSION_RISK")
    if shape_class == "SHAPE_DUAL_LOBE":
        warnings.append("DUAL_LOBE_SIGNAL_PRESENT")
    if fracture_status == "FAMILY_SPLIT_READY":
        warnings.append("FRACTURE_SPLIT_READY_PRESENT")

    return {
        "family_id": family_id,
        "pressure_state": state,
        "scorecard": {
            "diagnostic_scale": "0_to_1_comparative_not_probability",
            "stability_index": stability_index,
            "stretch_pressure_index": stretch_pressure,
            "dual_center_pressure_index": dual_center_pressure,
            "instability_pressure_index": instability_pressure,
            "boundary_tension_index": boundary_tension,
            "fission_pressure_index": fission_pressure,
        },
        "signals": signals,
        "warnings": sorted(set(warnings)),
        "explanation_lines": explanation_lines,
    }
