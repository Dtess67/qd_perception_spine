from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


class BranchStrength(str, Enum):
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"


class TemporalStatus(str, Enum):
    MINUS_ALIGNED = "minus_aligned"
    PLUS_ALIGNED = "plus_aligned"
    MIXED = "mixed"
    SPARSE = "sparse"
    CONFLICTING = "conflicting"


class SubstrateStatus(str, Enum):
    USABLE = "usable"
    DEGRADED = "degraded"
    COLLAPSE_BLOCKING = "collapse_blocking"


class CorrectiveSuppressionStatus(str, Enum):
    ADVISORY = "advisory"
    CAUTION_INDUCING = "caution_inducing"
    COLLAPSE_BLOCKING = "collapse_blocking"


class ContradictionPressure(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKING = "blocking"


class PriorStateQuality(str, Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    MISSING = "missing"


class OutputClass(str, Enum):
    RESOLVED_MINUS_1 = "resolved_minus_1"
    RESOLVED_PLUS_1 = "resolved_plus_1"
    CONDITIONAL_ANSWER = "conditional_answer"
    LIMITED_CAUTION_ANSWER = "limited_caution_answer"
    EXTERNAL_HOLD = "external_hold"


@dataclass(frozen=True)
class ManualTraceInputV0:
    delta_description: str
    minus_branch_strength: BranchStrength
    plus_branch_strength: BranchStrength
    past_recall_status: TemporalStatus
    future_projection_status: TemporalStatus
    substrate_status: SubstrateStatus
    corrective_suppression_status: CorrectiveSuppressionStatus
    contradiction_pressure: ContradictionPressure
    prior_state_quality: PriorStateQuality
    named_conditions: list[str] = field(default_factory=list)


def resolve_manual_decision_trace_v0_0(
    trace_input: ManualTraceInputV0 | Mapping[str, Any],
) -> dict[str, Any]:
    """
    Resolve one explicit manual decision trace with deterministic, fail-closed rules.

    This resolver is intentionally isolated from all runtime evidence/consumer surfaces.
    """
    try:
        normalized = _normalize_input(trace_input)
    except ValueError as exc:
        return _hold_result(
            reason_line=f"Input invalid: {exc}",
            blocking_reasons=["INPUT_INVALID"],
            applied_weight_notes=["FAIL_CLOSED_ON_INVALID_INPUT"],
        )

    rationale_lines: list[str] = []
    blocking_reasons: list[str] = []
    applied_weight_notes: list[str] = []

    if normalized.substrate_status == SubstrateStatus.COLLAPSE_BLOCKING:
        rationale_lines.append("Substrate status is collapse_blocking; collapse is not allowed.")
        blocking_reasons.append("SUBSTRATE_COLLAPSE_BLOCKING")
    if normalized.corrective_suppression_status == CorrectiveSuppressionStatus.COLLAPSE_BLOCKING:
        rationale_lines.append("Corrective suppression is collapse_blocking; collapse is not allowed.")
        blocking_reasons.append("CORRECTIVE_SUPPRESSION_COLLAPSE_BLOCKING")
    if normalized.contradiction_pressure in (ContradictionPressure.HIGH, ContradictionPressure.BLOCKING):
        rationale_lines.append("Contradiction pressure is high/blocking; collapse is not allowed.")
        blocking_reasons.append("CONTRADICTION_BLOCKING")

    if blocking_reasons:
        applied_weight_notes.append("FAIL_CLOSED_ON_BLOCKING_GUARDRAILS")
        return _result(
            output_class=OutputClass.EXTERNAL_HOLD,
            rationale_lines=rationale_lines,
            collapse_allowed=False,
            blocking_reasons=blocking_reasons,
            applied_weight_notes=applied_weight_notes,
        )

    minus_rank = _strength_rank(normalized.minus_branch_strength)
    plus_rank = _strength_rank(normalized.plus_branch_strength)
    dominant_branch: str | None
    if minus_rank > plus_rank:
        dominant_branch = "minus"
    elif plus_rank > minus_rank:
        dominant_branch = "plus"
    else:
        dominant_branch = None

    past_supports_dominant = (
        (dominant_branch == "plus" and normalized.past_recall_status == TemporalStatus.PLUS_ALIGNED)
        or (dominant_branch == "minus" and normalized.past_recall_status == TemporalStatus.MINUS_ALIGNED)
    )

    projection_aligns_dominant = (
        (dominant_branch == "plus" and normalized.future_projection_status == TemporalStatus.PLUS_ALIGNED)
        or (dominant_branch == "minus" and normalized.future_projection_status == TemporalStatus.MINUS_ALIGNED)
    )
    projection_primary_without_grounded = projection_aligns_dominant and not past_supports_dominant
    projection_upgrade_blocked = (
        dominant_branch is not None
        and projection_primary_without_grounded
        and (
            normalized.past_recall_status in (TemporalStatus.SPARSE, TemporalStatus.CONFLICTING)
            or normalized.substrate_status == SubstrateStatus.DEGRADED
        )
    )
    if projection_upgrade_blocked:
        applied_weight_notes.append("PROJECTION_ALONE_UPGRADE_BLOCKED")

    caution_pressure = (
        normalized.substrate_status == SubstrateStatus.DEGRADED
        or normalized.corrective_suppression_status == CorrectiveSuppressionStatus.CAUTION_INDUCING
        or normalized.prior_state_quality in (PriorStateQuality.WEAK, PriorStateQuality.MISSING)
        or normalized.contradiction_pressure == ContradictionPressure.MEDIUM
    )
    if caution_pressure:
        applied_weight_notes.append("CAUTION_PRESSURE_ACTIVE")

    past_conflicts_dominant = (
        (dominant_branch == "plus" and normalized.past_recall_status == TemporalStatus.MINUS_ALIGNED)
        or (dominant_branch == "minus" and normalized.past_recall_status == TemporalStatus.PLUS_ALIGNED)
        or normalized.past_recall_status == TemporalStatus.CONFLICTING
    )

    degraded_strong_grounded_exception = (
        normalized.substrate_status == SubstrateStatus.DEGRADED
        and dominant_branch is not None
        and abs(minus_rank - plus_rank) >= 2
        and past_supports_dominant
        and normalized.corrective_suppression_status == CorrectiveSuppressionStatus.ADVISORY
        and normalized.prior_state_quality in (PriorStateQuality.STRONG, PriorStateQuality.MODERATE)
        and normalized.contradiction_pressure == ContradictionPressure.LOW
        and not past_conflicts_dominant
    )
    strictness_blocks_resolve = caution_pressure and not degraded_strong_grounded_exception

    can_resolve = (
        dominant_branch is not None
        and abs(minus_rank - plus_rank) >= 1
        and not projection_upgrade_blocked
        and not strictness_blocks_resolve
        and not past_conflicts_dominant
        and normalized.past_recall_status != TemporalStatus.SPARSE
        and normalized.contradiction_pressure == ContradictionPressure.LOW
    )

    if can_resolve:
        output_class = (
            OutputClass.RESOLVED_MINUS_1 if dominant_branch == "minus" else OutputClass.RESOLVED_PLUS_1
        )
        rationale_lines.append("Dominant branch present with non-blocking grounded support.")
        rationale_lines.append("No caution/blocking modifiers prevent resolved collapse.")
        return _result(
            output_class=output_class,
            rationale_lines=rationale_lines,
            collapse_allowed=True,
            blocking_reasons=[],
            applied_weight_notes=applied_weight_notes,
        )

    has_named_conditions = bool(normalized.named_conditions)
    if dominant_branch is not None and has_named_conditions:
        rationale_lines.append("Directional candidate exists but requires explicit named conditions.")
        if projection_upgrade_blocked:
            rationale_lines.append("Projection-alone upgrade remains blocked under current recall/substrate context.")
        return _result(
            output_class=OutputClass.CONDITIONAL_ANSWER,
            rationale_lines=rationale_lines,
            collapse_allowed=False,
            blocking_reasons=[],
            applied_weight_notes=applied_weight_notes,
        )

    if dominant_branch is None or caution_pressure or projection_upgrade_blocked or past_conflicts_dominant:
        rationale_lines.append("Signal remains mixed/limited under caution or ambiguity.")
        return _result(
            output_class=OutputClass.LIMITED_CAUTION_ANSWER,
            rationale_lines=rationale_lines,
            collapse_allowed=False,
            blocking_reasons=[],
            applied_weight_notes=applied_weight_notes,
        )

    return _hold_result(
        reason_line="Fail-closed: output class not earned under current qualitative rules.",
        blocking_reasons=["AMBIGUOUS_UNDERSPECIFIED_CASE"],
        applied_weight_notes=applied_weight_notes + ["FAIL_CLOSED_AMBIGUOUS"],
    )


def _normalize_input(raw: ManualTraceInputV0 | Mapping[str, Any]) -> ManualTraceInputV0:
    if isinstance(raw, ManualTraceInputV0):
        _validate_named_conditions(raw.named_conditions)
        delta_description = raw.delta_description
        if not isinstance(delta_description, str) or not delta_description.strip():
            raise ValueError("delta_description must be non-empty str.")
        return ManualTraceInputV0(
            delta_description=delta_description,
            minus_branch_strength=BranchStrength(raw.minus_branch_strength),
            plus_branch_strength=BranchStrength(raw.plus_branch_strength),
            past_recall_status=TemporalStatus(raw.past_recall_status),
            future_projection_status=TemporalStatus(raw.future_projection_status),
            substrate_status=SubstrateStatus(raw.substrate_status),
            corrective_suppression_status=CorrectiveSuppressionStatus(raw.corrective_suppression_status),
            contradiction_pressure=ContradictionPressure(raw.contradiction_pressure),
            prior_state_quality=PriorStateQuality(raw.prior_state_quality),
            named_conditions=list(raw.named_conditions),
        )

    if not isinstance(raw, Mapping):
        raise ValueError("trace_input must be ManualTraceInputV0 or mapping.")

    required = [
        "delta_description",
        "minus_branch_strength",
        "plus_branch_strength",
        "past_recall_status",
        "future_projection_status",
        "substrate_status",
        "corrective_suppression_status",
        "contradiction_pressure",
        "prior_state_quality",
    ]
    missing = [k for k in required if k not in raw]
    if missing:
        raise ValueError(f"missing required fields: {', '.join(missing)}")

    conditions = raw.get("named_conditions", [])
    _validate_named_conditions(conditions)

    delta_description = raw["delta_description"]
    if not isinstance(delta_description, str) or not delta_description.strip():
        raise ValueError("delta_description must be non-empty str.")

    return ManualTraceInputV0(
        delta_description=delta_description,
        minus_branch_strength=BranchStrength(raw["minus_branch_strength"]),
        plus_branch_strength=BranchStrength(raw["plus_branch_strength"]),
        past_recall_status=TemporalStatus(raw["past_recall_status"]),
        future_projection_status=TemporalStatus(raw["future_projection_status"]),
        substrate_status=SubstrateStatus(raw["substrate_status"]),
        corrective_suppression_status=CorrectiveSuppressionStatus(raw["corrective_suppression_status"]),
        contradiction_pressure=ContradictionPressure(raw["contradiction_pressure"]),
        prior_state_quality=PriorStateQuality(raw["prior_state_quality"]),
        named_conditions=list(conditions),
    )


def _validate_named_conditions(conditions: Any) -> None:
    if not isinstance(conditions, list):
        raise ValueError("named_conditions must be list[str].")
    if any((not isinstance(item, str) or not item.strip()) for item in conditions):
        raise ValueError("named_conditions entries must be non-empty str.")


def _strength_rank(strength: BranchStrength) -> int:
    if strength == BranchStrength.NONE:
        return 0
    if strength == BranchStrength.WEAK:
        return 1
    if strength == BranchStrength.MODERATE:
        return 2
    return 3


def _hold_result(
    reason_line: str,
    blocking_reasons: list[str],
    applied_weight_notes: list[str],
) -> dict[str, Any]:
    return _result(
        output_class=OutputClass.EXTERNAL_HOLD,
        rationale_lines=[reason_line],
        collapse_allowed=False,
        blocking_reasons=blocking_reasons,
        applied_weight_notes=applied_weight_notes,
    )


def _result(
    output_class: OutputClass,
    rationale_lines: list[str],
    collapse_allowed: bool,
    blocking_reasons: list[str],
    applied_weight_notes: list[str],
) -> dict[str, Any]:
    return {
        "output_class": output_class.value,
        "rationale_lines": rationale_lines,
        "collapse_allowed": collapse_allowed,
        "blocking_reasons": blocking_reasons,
        "applied_weight_notes": applied_weight_notes,
        "lineage_mutation_performed": False,
        "event_creation_performed": False,
        "history_rewrite_performed": False,
    }


def manual_trace_input_to_dict(trace_input: ManualTraceInputV0) -> dict[str, Any]:
    data = asdict(_normalize_input(trace_input))
    return {
        "delta_description": data["delta_description"],
        "minus_branch_strength": data["minus_branch_strength"].value,
        "plus_branch_strength": data["plus_branch_strength"].value,
        "past_recall_status": data["past_recall_status"].value,
        "future_projection_status": data["future_projection_status"].value,
        "substrate_status": data["substrate_status"].value,
        "corrective_suppression_status": data["corrective_suppression_status"].value,
        "contradiction_pressure": data["contradiction_pressure"].value,
        "prior_state_quality": data["prior_state_quality"].value,
        "named_conditions": data["named_conditions"],
    }
