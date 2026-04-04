from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PatternPlacement:
    """
    Represents a single structural placement of a neutral state vector in a specific region.
    This is used to track repeated structural patterns over time.
    """
    scenario_name: str
    event_index: int
    region_id: str
    axis_a: float
    axis_b: float
    axis_c: float
    axis_d: float

@dataclass
class PatternFamilySummary:
    """
    Summarizes a grouped set of structural placements (a 'family') to assess stability 
    and determine if a neutral symbol (glyph) has been 'earned'.
    """
    family_id: str
    dominant_region_id: str
    placement_count: int
    stability_score: float
    glyph_id: Optional[str]
    rationale: str

class PatternFamilyAnalyzer:
    """
    Analyzes sequences of structural placements to identify stable pattern families.
    It tracks how often patterns land in the same region and assigns neutral glyphs
    once stability thresholds are met.
    """

    def __init__(self):
        # Maps family_id to a list of PatternPlacement objects
        self._families = {}
        
        # Simple threshold for earning a glyph
        self.MIN_PLACEMENTS_FOR_GLYPH = 3
        self.STABILITY_THRESHOLD_FOR_GLYPH = 0.7

    def record_placement(self, family_id: str, placement: PatternPlacement) -> None:
        """
        Adds a new placement to a specific family for analysis.
        """
        if family_id not in self._families:
            self._families[family_id] = []
        self._families[family_id].append(placement)

    def placements_for_family(self, family_id: str) -> List[PatternPlacement]:
        """
        Returns all recorded placements for a given family.
        """
        return self._families.get(family_id, [])

    def summarize_family(self, family_id: str) -> PatternFamilySummary:
        """
        Analyzes the recorded placements for a family and produces a summary,
        including stability scores and potential glyph assignment.
        """
        placements = self.placements_for_family(family_id)
        
        if not placements:
            return PatternFamilySummary(
                family_id=family_id,
                dominant_region_id="none",
                placement_count=0,
                stability_score=0.0,
                glyph_id=None,
                rationale="No placements recorded for this family."
            )

        # Count occurrences of each region_id
        region_counts = {}
        for p in placements:
            region_counts[p.region_id] = region_counts.get(p.region_id, 0) + 1

        # Identify the dominant region
        dominant_region_id = max(region_counts, key=region_counts.get)
        dominant_count = region_counts[dominant_region_id]
        total_count = len(placements)

        # Calculate stability_score: percentage of placements in the dominant region
        stability_score = float(dominant_count) / float(total_count)
        
        # Clamp stability score (though it's naturally 0-1 here)
        stability_score = max(0.0, min(1.0, stability_score))

        # Determine glyph earning
        glyph_id = None
        if total_count >= self.MIN_PLACEMENTS_FOR_GLYPH and stability_score >= self.STABILITY_THRESHOLD_FOR_GLYPH:
            # Map family_id to a neutral glyph ID deterministically for the demo
            # In a real system, these would be assigned from a pool
            glyph_map = {
                "family_gradual_rise": "glyph_01",
                "family_spike": "glyph_02",
                "family_stable": "glyph_03"
            }
            glyph_id = glyph_map.get(family_id, "glyph_unknown")

        # Create rationale
        rationale = (
            f"Analyzed {total_count} placements. Dominant region '{dominant_region_id}' "
            f"appeared in {dominant_count} cases. Stability score is {stability_score:.2f}."
        )
        
        if glyph_id:
            rationale += f" Thresholds met; assigned {glyph_id}."
        elif total_count < self.MIN_PLACEMENTS_FOR_GLYPH:
            rationale += f" Not enough data for glyph (need {self.MIN_PLACEMENTS_FOR_GLYPH})."
        elif stability_score < self.STABILITY_THRESHOLD_FOR_GLYPH:
            rationale += f" Stability too low for glyph (need {self.STABILITY_THRESHOLD_FOR_GLYPH})."

        return PatternFamilySummary(
            family_id=family_id,
            dominant_region_id=dominant_region_id,
            placement_count=total_count,
            stability_score=stability_score,
            glyph_id=glyph_id,
            rationale=rationale
        )
