from types import SimpleNamespace

from qd_perception.delta_frame import DeltaFrame
from qd_perception.feature_frame import FeatureFrame
from qd_perception.neutral_state_vector import NeutralStateMapper
from qd_perception.perception_pipeline import PerceptionPipeline
from qd_perception.proto_concept import (
    ProtoConcept,
    ProtoConceptAssigner,
    ProtoStructuralSignatureV1,
)
from qd_perception.sensor_event import SensorEvent


def test_proto_assigner_emits_structural_signatures_for_known_cases():
    assigner = ProtoConceptAssigner()

    cases = [
        (
            FeatureFrame("s", "c", "rising", "high", "spike", "novel"),
            "sudden_rise",
            (1, 2, 2, 1, 0),
        ),
        (
            FeatureFrame("s", "c", "falling", "high", "spike", "familiar"),
            "sudden_drop",
            (-1, 2, 2, 0, 0),
        ),
        (
            FeatureFrame("s", "c", "steady", "low", "steady", "familiar"),
            "stable_signal",
            (0, 0, 0, 0, 0),
        ),
        (
            FeatureFrame("s", "c", "rising", "medium", "drift", "novel"),
            "gradual_shift",
            (1, 1, 1, 1, 0),
        ),
        (
            FeatureFrame("s", "c", "rising", "high", "drift", "novel"),
            "unresolved_pattern",
            (1, 9, 2, 1, 1),
        ),
    ]

    for frame, expected_name, expected_codes in cases:
        concept = assigner.assign(frame)
        assert isinstance(concept.signature, ProtoStructuralSignatureV1)
        assert concept.name == expected_name
        assert (
            concept.signature.direction_code,
            concept.signature.change_mode_code,
            concept.signature.magnitude_band_code,
            concept.signature.novelty_code,
            concept.signature.resolution_code,
        ) == expected_codes
        assert concept.confidence == concept.signature.confidence


def test_pipeline_status_mapping_uses_structural_signature_not_name():
    pipeline = PerceptionPipeline()
    delta = DeltaFrame("s", "c", 1.0, 2.0, 1.0, "rising", 1.0, 1.0, False)

    rise_signature = ProtoStructuralSignatureV1(
        direction_code=1,
        change_mode_code=2,
        magnitude_band_code=2,
        novelty_code=1,
        resolution_code=0,
        confidence=0.9,
    )
    mismatch_name = ProtoConcept(
        signature=rise_signature,
        name="unresolved_pattern",
        confidence=0.9,
        rationale="name intentionally mismatched",
    )
    status_code, _ = pipeline._map_status(delta, mismatch_name)
    assert status_code == "SUDDEN_RISE"

    unresolved_signature = ProtoStructuralSignatureV1(
        direction_code=0,
        change_mode_code=0,
        magnitude_band_code=0,
        novelty_code=0,
        resolution_code=1,
        confidence=0.5,
    )
    mismatch_name = ProtoConcept(
        signature=unresolved_signature,
        name="stable_signal",
        confidence=0.5,
        rationale="name intentionally mismatched",
    )
    status_code, _ = pipeline._map_status(delta, mismatch_name)
    assert status_code == "UNRESOLVED_PATTERN"


def test_neutral_mapper_outcome_is_signature_driven_not_name_driven():
    mapper = NeutralStateMapper()
    delta = DeltaFrame("s", "c", 1.0, 10.0, 9.0, "rising", 9.0, 90.0, True)
    signature = ProtoStructuralSignatureV1(
        direction_code=1,
        change_mode_code=2,
        magnitude_band_code=2,
        novelty_code=1,
        resolution_code=0,
        confidence=0.9,
    )

    result_a = SimpleNamespace(
        delta_frame=delta,
        proto_concept=ProtoConcept(signature, "sudden_rise", 0.9, "A"),
    )
    result_b = SimpleNamespace(
        delta_frame=delta,
        proto_concept=ProtoConcept(signature, "not_the_authoritative_field", 0.9, "B"),
    )

    vec_a = mapper.map(result_a)
    vec_b = mapper.map(result_b)

    assert vec_a == vec_b


def test_status_behavior_for_rise_drop_unresolved_is_preserved():
    pipeline = PerceptionPipeline()

    # Rise spike
    e1 = SensorEvent("s", "c", 0.0, 0.0)
    e2 = SensorEvent("s", "c", 1.0, 10.0)
    rise = pipeline.run(e1, e2)
    assert rise.status_code == "SUDDEN_RISE"

    # Drop spike
    e3 = SensorEvent("s", "c", 2.0, 0.0)
    drop = pipeline.run(e2, e3)
    assert drop.status_code == "SUDDEN_DROP"

    # Unresolved: high + drift (not spike), should remain unresolved
    e4 = SensorEvent("s", "c", 3.0, 2.1)
    unresolved = pipeline.run(e3, e4)
    assert unresolved.status_code == "UNRESOLVED_PATTERN"
