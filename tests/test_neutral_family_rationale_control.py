from qd_perception.neutral_family_memory_v1 import FamilyDecision, NeutralFamilyMemoryV1


def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def _spread(v: float = 0.01) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}


def test_rationale_text_alone_does_not_change_hold_lane():
    memory = NeutralFamilyMemoryV1()
    memory.join_or_create_family("sym_seed", _sig(0.1), _spread(), 10)

    def _decision_with_rationale(rationale_text: str) -> FamilyDecision:
        return FamilyDecision(
            status="FAMILY_HOLD",
            family_id="fam_01",
            symbol_id="sym_edge_case",
            confidence=0.2,
            rationale=rationale_text,
            hold_mode="EDGE_BAND_PROXIMITY",
        )

    # First call with rationale that contains the old prose trigger phrase.
    memory.evaluate_symbol = lambda symbol_id, signature, spread: _decision_with_rationale(
        "Symbol in borderline band; hold."
    )
    memory.join_or_create_family("sym_edge_case", _sig(0.7), _spread(), 1)

    # Second call uses different wording with no trigger phrase.
    memory.evaluate_symbol = lambda symbol_id, signature, spread: _decision_with_rationale(
        "Wording changed completely; still the same structural hold mode."
    )
    memory.join_or_create_family("sym_edge_case", _sig(0.7), _spread(), 1)

    assert memory._pending_edge["sym_edge_case"]["fam_01"] == 2
    assert "sym_edge_case" in memory._pending_kinship
    assert "fam_01" not in memory._pending_kinship["sym_edge_case"]


def test_structured_hold_mode_controls_lane_even_if_rationale_mentions_borderline():
    memory = NeutralFamilyMemoryV1()
    memory.join_or_create_family("sym_seed", _sig(0.1), _spread(), 10)

    memory.evaluate_symbol = lambda symbol_id, signature, spread: FamilyDecision(
        status="FAMILY_HOLD",
        family_id="fam_01",
        symbol_id="sym_join_case",
        confidence=0.5,
        rationale="Contains borderline band text but is not an edge hold mode.",
        hold_mode="JOIN_PERSISTENCE",
    )
    memory.join_or_create_family("sym_join_case", _sig(0.12), _spread(), 1)

    assert memory._pending_kinship["sym_join_case"]["fam_01"] == 1
    assert (
        "sym_join_case" not in memory._pending_edge
        or "fam_01" not in memory._pending_edge.get("sym_join_case", {})
    )


def test_evaluate_symbol_sets_structured_hold_modes_for_both_hold_cases():
    memory = NeutralFamilyMemoryV1()
    memory.join_or_create_family("sym_seed", _sig(0.1), _spread(), 10)

    # Join-distance hold path (requires persistence).
    join_hold = memory.evaluate_symbol("sym_join", _sig(0.12), _spread())
    assert join_hold.status == "FAMILY_HOLD"
    assert join_hold.hold_mode == "JOIN_PERSISTENCE"

    # Borderline hold path (edge-proximity persistence).
    edge_hold_sig = {"axis_a": 0.9, "axis_b": 0.1, "axis_c": 0.1, "axis_d": 0.1}
    edge_hold = memory.evaluate_symbol("sym_edge", edge_hold_sig, _spread())
    assert edge_hold.status == "FAMILY_HOLD"
    assert edge_hold.hold_mode == "EDGE_BAND_PROXIMITY"
