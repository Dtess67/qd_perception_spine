from dataclasses import dataclass
from typing import Optional
from .sensor_event import SensorEvent
from .delta_frame import DeltaFrame, DeltaCalculator
from .feature_frame import FeatureFrame, FeatureExtractor
from .proto_concept import ProtoConcept, ProtoConceptAssigner

@dataclass
class PerceptionResult:
    """
    The end-to-end result of processing a single sensor event.
    Includes the original event and all derived analytical layers.
    """
    event: SensorEvent
    delta_frame: DeltaFrame
    feature_frame: FeatureFrame
    proto_concept: ProtoConcept
    status_code: str
    status_label: str

class PerceptionPipeline:
    """
    Coordinates the transformation of a raw SensorEvent into a high-level ProtoConcept.
    This is the main entry point for the perception subsystem.
    """
    def __init__(self):
        # Initialize internal processing stages
        self.delta_calculator = DeltaCalculator()
        self.feature_extractor = FeatureExtractor()
        self.proto_assigner = ProtoConceptAssigner()

    def run(self, previous_event: Optional[SensorEvent], current_event: SensorEvent) -> PerceptionResult:
        """
        Executes the three-stage perception process:
        1. Delta Calculation (difference tracking)
        2. Feature Extraction (categorization)
        3. Proto-Concept Assignment (high-level identification)
        """
        # Stage 1: Compute Change
        delta_frame = self.delta_calculator.compute(previous_event, current_event)
        
        # Stage 2: Extract Qualitative Features
        feature_frame = self.feature_extractor.from_delta(delta_frame)
        
        # Stage 3: Assign Mental Label (Proto-Concept)
        proto_concept = self.proto_assigner.assign(feature_frame)

        # Determine Status Code and Label based on the result
        status_code, status_label = self._map_status(delta_frame, proto_concept)

        # Return the consolidated result
        return PerceptionResult(
            event=current_event,
            delta_frame=delta_frame,
            feature_frame=feature_frame,
            proto_concept=proto_concept,
            status_code=status_code,
            status_label=status_label
        )

    def _map_status(self, delta_frame: DeltaFrame, proto_concept: ProtoConcept) -> tuple[str, str]:
        """
        Maps the current perception state to a concise status code and label.
        """
        # If it's the very first event, that's a primary status
        if delta_frame.previous_value is None:
            return "FIRST_EVENT", "First sensor event received"

        # Map based on the identified proto-concept
        name = proto_concept.name

        if name == "stable_signal":
            return "STABLE_SIGNAL", "Signal is stable and familiar"
        elif name == "gradual_shift":
            return "GRADUAL_SHIFT", "Detected a gradual change in signal"
        elif name == "sudden_rise":
            return "SUDDEN_RISE", "Detected a sharp upward spike"
        elif name == "sudden_drop":
            return "SUDDEN_DROP", "Detected a sharp downward drop"
        elif name == "unresolved_pattern":
            return "UNRESOLVED_PATTERN", "Signal pattern could not be determined"
        
        # Fallback for unexpected proto-concept names
        return "SUCCESS", "Successful perception processing"
