from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from datetime import datetime, timezone
import json
import os
import math
from qd_perception.family_pressure_forecast_v1 import evaluate_family_pressure_forecast

@dataclass
class FamilyDecision:
    """
    Represents the outcome of a neutral symbol family evaluation.
    
    Fields:
    - status: str (NEW_FAMILY, JOIN_EXISTING_FAMILY, NO_FAMILY_MATCH, FAMILY_HOLD, 
                  FAMILY_TENSION, FAMILY_BRIDGE, FAMILY_EDGE, FAMILY_FRACTURE_HOLD, 
                  FAMILY_SPLIT_READY)
    - family_id: Optional[str]
    - symbol_id: str
    - confidence: float (0.0 to 1.0)
    - rationale: str (Structural explanation of the decision)
    """
    status: str
    family_id: Optional[str]
    symbol_id: str
    confidence: float
    rationale: str

@dataclass
class NeutralFamilyRecordV1:
    """
    A persistent record of a neutral higher-order structural family.
    
    Fields:
    - family_id: Unique neutral ID (fam_01, fam_02, etc.)
    - member_symbol_ids: List of symbols that belong to this family.
    - mint_signature: The structural centroid of the family when it was first earned.
    - current_signature: The weighted average centroid of all current members.
    - mint_spread: The structural envelope of the family when it was first earned.
    - current_spread: The average structural envelope of all current members.
    - observation_count: Total number of observations from all member symbols.
    - fracture_counter: Number of consecutive observations exceeding coherence.
    - fracture_status: Current fracture-related status (None, FAMILY_FRACTURE_HOLD, etc.)
    - subgroup_count: Detected number of structural internal centers (default 1).
    - subgroup_evidence_counter: Persistence counter for detected internal separation.
    - lifecycle_status: Whether this family is active for membership decisions.
    - inactive_reason: Structural reason for inactivation (if any).
    - historical_member_symbol_ids: Snapshot of members at inactivation (if any).
    - lineage_parent_family_id: Parent family ID if this family was created as a successor.
    - lineage_parent_family_ids: Parent family IDs if this family was created by reunion.
    - lineage_successor_family_ids: Successor family IDs if this family fissioned.
    - lineage_fission_event_id: Fission event ID that created this family (successor only).
    - lineage_reunion_event_id: Reunion event ID that created this family (successor only).
    - fission_event_ids: Fission event IDs associated with this family (parent or successor).
    - reunion_event_ids: Reunion event IDs associated with this family (source or successor).
    - fission_candidate_counter: Consecutive stable observations supporting actual fission.
    - fission_partition_key: Canonical stable key representing the current subgroup partition.
    
    Backward-compatibility aliases:
    - combined_signature -> current_signature
    - combined_spread -> current_spread
    """
    family_id: str
    member_symbol_ids: List[str]
    mint_signature: dict[str, float]
    current_signature: dict[str, float]
    mint_spread: dict[str, float]
    current_spread: dict[str, float]
    observation_count: int
    fracture_counter: int = 0
    fracture_status: Optional[str] = None
    subgroup_count: int = 1
    subgroup_evidence_counter: int = 0
    lifecycle_status: str = "FAMILY_ACTIVE"
    inactive_reason: Optional[str] = None
    historical_member_symbol_ids: List[str] = field(default_factory=list)
    lineage_parent_family_id: Optional[str] = None
    lineage_parent_family_ids: List[str] = field(default_factory=list)
    lineage_successor_family_ids: List[str] = field(default_factory=list)
    lineage_fission_event_id: Optional[str] = None
    lineage_reunion_event_id: Optional[str] = None
    fission_event_ids: List[str] = field(default_factory=list)
    reunion_event_ids: List[str] = field(default_factory=list)
    fission_candidate_counter: int = 0
    fission_partition_key: Optional[str] = None

    # Aliases to preserve existing callers/tests without changing semantics
    @property
    def combined_signature(self) -> dict[str, float]:
        return self.current_signature

    @property
    def combined_spread(self) -> dict[str, float]:
        return self.current_spread

class NeutralFamilyMemoryV1:
    """
    Higher-order grouping layer for persistent neutral symbols.
    
    This layer allows symbols to belong to a family (kinship) based on 
    structural proximity in the axis space, without collapsing 
    their individual identities.
    """
    
    # Thresholds for family formation and membership
    # These are provisional heuristics for structural kinship
    DISTANCE_THRESHOLD = 0.15 # Max distance between centroids to consider kinship
    HOLD_THRESHOLD = 0.25     # Plausible but uncertain kinship band
    JOIN_PERSISTENCE_THRESHOLD = 2 # Required repeated observations for kinship earning
    BRIDGE_PERSISTENCE_THRESHOLD = 3 # Required repeated tension events for bridge status
    EDGE_PERSISTENCE_THRESHOLD = 3   # Required repeated boundary events for edge status
    SPREAD_COMPATIBILITY_FACTOR = 2.0 # Multiplier for spread to allow overlap
    TENSION_MARGIN_THRESHOLD = 0.05   # Min distance difference required to resolve tension
    MAX_COHERENCE_SPREAD = 0.35        # Max allowed average spread before fracture risk
    INTERNAL_DISTANCE_THRESHOLD = 0.4 # Max distance between members before fracture risk
    FRACTURE_PERSISTENCE_THRESHOLD = 3 # Required hits to reach SPLIT_READY
    SUBGROUP_SEPARATION_THRESHOLD = 0.25 # Distance margin required to suspect dual centers
    SUBGROUP_PERSISTENCE_THRESHOLD = 3  # Required observations to confirm internal bifurcation
    SUBGROUP_TIGHTNESS_RATIO = 2.0 # Separation must be 2x greater than internal spread
    # Conservative "actual fission" thresholds (v1)
    MIN_MEMBERS_FOR_FISSION = 6           # Under-splitting bias: avoid fission on tiny families
    FISSION_PERSISTENCE_THRESHOLD = 3     # Additional persistence beyond SPLIT_READY + subgroup_count==2
    MIN_SUBGROUP_MEMBERS_FOR_DETECTION = 2  # Fail closed: ignore one-off outlier partitions
    MIN_SUBGROUP_MEMBERS_FOR_FISSION = 3    # Refuse fission unless both successors have earned bulk
    # Conservative "actual reunion" thresholds (v1)
    REUNION_CENTER_DISTANCE_THRESHOLD = 0.10   # Families must be very close to be reunion candidates
    REUNION_SPREAD_DELTA_THRESHOLD = 0.08      # Family average spread mismatch must remain small
    REUNION_PERSISTENCE_THRESHOLD = 4          # Repeated structural closeness required
    REUNION_COMBINED_MAX_SPREAD = 0.30         # Reunited family must remain coherent by spread
    REUNION_COMBINED_MAX_INTERNAL_DISTANCE = 0.30  # Reunited members must remain structurally compact
    MIN_MEMBERS_PER_SOURCE_FOR_REUNION = 2     # Refuse reunion from tiny source families
    # Geometric fit/residual audit thresholds (provisional heuristics)
    GEOMETRY_FIT_CENTER_RESIDUAL_MAX = 0.03
    GEOMETRY_FIT_CENTER_RESIDUAL_RATIO_MAX = 0.35
    GEOMETRY_FIT_SPREAD_RESIDUAL_MAX = 0.03
    GEOMETRY_FIT_SPREAD_RESIDUAL_RATIO_MAX = 0.60
    GEOMETRY_FIT_SCORE_DECAY_MAX = 1.50
    TRANSITION_CONTINUITY_CENTER_RESIDUAL_MAX = 0.08
    # Topology residual / shape-class audit thresholds (provisional heuristics)
    TOPOLOGY_MIN_MEMBERS = 4
    TOPOLOGY_COMPACT_ANISOTROPY_MAX = 1.80
    TOPOLOGY_COMPACT_PAIRWISE_RATIO_MAX = 1.60
    TOPOLOGY_ELONGATED_ANISOTROPY_MIN = 2.50
    TOPOLOGY_ELONGATED_PAIRWISE_RATIO_MIN = 2.00
    # Family pressure forecast thresholds (provisional heuristics)
    PRESSURE_MIN_MEMBERS = 4
    PRESSURE_RECENT_TRANSITION_WINDOW = 3
    PRESSURE_STRETCHED_THRESHOLD = 0.55
    PRESSURE_DUAL_CENTER_THRESHOLD = 0.70
    PRESSURE_INSTABILITY_THRESHOLD = 0.65
    PRESSURE_FISSION_PRONE_THRESHOLD = 0.75
    PRESSURE_STABLE_THRESHOLD = 0.60
    DURABLE_LEDGER_DEFAULT_PATH = "runs/family_transition_event_ledger_v1.jsonl"
    
    def __init__(self, durable_ledger_path: Optional[str] = None):
        # Storage for family records, keyed by family_id
        self._families: dict[str, NeutralFamilyRecordV1] = {}
        # Mapping from symbol_id to signature/spread (for internal structural analysis)
        self._symbol_signatures: dict[str, dict[str, float]] = {}
        self._symbol_spreads: dict[str, dict[str, float]] = {}
        # Mapping from symbol_id to family_id (one symbol -> one primary family)
        self._symbol_to_family: dict[str, str] = {}
        # Tracking for pending kinship candidates (persistence counter)
        # symbol_id -> {family_id: count}
        self._pending_kinship: dict[str, dict[str, int]] = {}
        # Tracking for pending multi-family bridge events
        # symbol_id -> count of tension observations
        self._pending_bridge: dict[str, int] = {}
        # Tracking for pending single-family edge events
        # symbol_id -> {family_id: count}
        self._pending_edge: dict[str, dict[str, int]] = {}
        # Storage for earned persistent boundary/bridge statuses (symbol_id -> status_str)
        self._earned_boundary_statuses: dict[str, str] = {}
        # Counter for generating new neutral family IDs
        self._family_counter = 0
        # Fission event log (in-process audit trail)
        self._fission_event_counter = 0
        self._fission_events: list[dict] = []
        # Reunion event log (in-process audit trail)
        self._reunion_event_counter = 0
        self._reunion_events: list[dict] = []
        # Pairwise persistence for reunion candidacy: "fam_a||fam_b" -> consecutive hits
        self._pending_reunion: dict[str, int] = {}
        # Durable event ledger configuration/state
        self._durable_ledger_path = durable_ledger_path or self.DURABLE_LEDGER_DEFAULT_PATH
        self._durable_written_event_ids: set[str] = set()
        self._durable_write_counter = 0

    def _calculate_distance(self, sig1: dict[str, float], sig2: dict[str, float]) -> float:
        """Calculates the structural distance between two signatures."""
        axes = ["axis_a", "axis_b", "axis_c", "axis_d"]
        total_dist = 0.0
        for axis in axes:
            total_dist += abs(sig1.get(axis, 0.0) - sig2.get(axis, 0.0))
        return total_dist / len(axes)

    def evaluate_symbol(self, symbol_id: str, signature: dict[str, float], spread: dict[str, float]) -> FamilyDecision:
        """
        Evaluates a symbol for potential family membership.
        
        Uses structural proximity (centroid distance and spread overlap) 
        to decide if the symbol should join an existing family or start a new one.
        """
        # If already in a family, return that
        if symbol_id in self._symbol_to_family:
            fam_id = self._symbol_to_family[symbol_id]
            record = self._families[fam_id]
            dist = self._calculate_distance(signature, record.current_signature)
            return FamilyDecision(
                status="JOIN_EXISTING_FAMILY",
                family_id=fam_id,
                symbol_id=symbol_id,
                confidence=1.0,
                rationale=f"Symbol {symbol_id} is already a member of {fam_id} at distance {dist:.3f}."
            )

        # 1. Look for existing family matches
        # We track all plausible candidates to detect multi-family tension
        plausible_candidates: list[tuple[str, float, bool, float]] = []
        
        for fam_id, record in self._families.items():
            if record.lifecycle_status != "FAMILY_ACTIVE":
                continue
            dist = self._calculate_distance(signature, record.current_signature)
            
            # Use family spread to explain the fit
            # We check if distance is within the average absolute deviation of the family
            avg_fam_spread = sum(record.current_spread.values()) / len(record.current_spread) if record.current_spread else 0.0
            is_inside_envelope = dist <= avg_fam_spread
            
            # Check if distance is within the hold band
            if dist <= self.HOLD_THRESHOLD:
                plausible_candidates.append((fam_id, dist, is_inside_envelope, avg_fam_spread))

        # Sort candidates by distance (closest first)
        plausible_candidates.sort(key=lambda x: x[1])

        # 2. Handle Multi-Family Tension
        if len(plausible_candidates) > 1:
            best_id, best_dist, best_inside, best_spread = plausible_candidates[0]
            next_id, next_dist, _, _ = plausible_candidates[1]
            
            # If the best match is not decisively better than the second best
            # Tension is only reported if both are within some "competing" range
            if (next_dist - best_dist) < self.TENSION_MARGIN_THRESHOLD:
                # Check for persistent bridge status
                hits = self._pending_bridge.get(symbol_id, 0) + 1
                if hits >= self.BRIDGE_PERSISTENCE_THRESHOLD:
                    return FamilyDecision(
                        status="FAMILY_BRIDGE",
                        family_id=None,
                        symbol_id=symbol_id,
                        confidence=0.6,
                        rationale=(f"Persistent structural tension ({hits} hits) between {best_id} and {next_id}. "
                                   f"Earned neutral BRIDGE status.")
                    )
                else:
                    return FamilyDecision(
                        status="FAMILY_TENSION",
                        family_id=None, # Explicitly unassigned due to tension
                        symbol_id=symbol_id,
                        confidence=0.1,
                        rationale=(f"Structural tension detected between {best_id} (dist={best_dist:.3f}) "
                                   f"and {next_id} (dist={next_dist:.3f}). Margin ({next_dist-best_dist:.3f}) "
                                   f"below threshold ({self.TENSION_MARGIN_THRESHOLD}). Hold for resolution.")
                    )

        # 3. If a potential match exists (and passed tension check), apply thresholds and persistence logic
        if plausible_candidates:
            best_family_id, min_dist, best_fam_inside, best_fam_spread = plausible_candidates[0]
            envelope_str = "inside" if best_fam_inside else "outside"
            
            # Check if it's within the strict join distance
            if min_dist < self.DISTANCE_THRESHOLD:
                # Still check persistence even if close, to ensure structural stability
                hits = self._pending_kinship.get(symbol_id, {}).get(best_family_id, 0) + 1
                if hits >= self.JOIN_PERSISTENCE_THRESHOLD:
                    return FamilyDecision(
                        status="JOIN_EXISTING_FAMILY",
                        family_id=best_family_id,
                        symbol_id=symbol_id,
                        confidence=1.0 - (min_dist / self.DISTANCE_THRESHOLD),
                        rationale=(f"Symbol {symbol_id} dist ({min_dist:.3f}) is {envelope_str} family envelope "
                                   f"({best_fam_spread:.3f}). Persistence ({hits}) earned join for {best_family_id}.")
                    )
                else:
                    return FamilyDecision(
                        status="FAMILY_HOLD",
                        family_id=best_family_id,
                        symbol_id=symbol_id,
                        confidence=0.5,
                        rationale=(f"Symbol {symbol_id} within join distance ({min_dist:.3f}, {envelope_str} envelope) "
                                   f"but requires more persistence ({hits}/{self.JOIN_PERSISTENCE_THRESHOLD}).")
                    )
            else:
                # Within the borderline/hold band
                # Check for persistent edge status
                edge_hits = self._pending_edge.get(symbol_id, {}).get(best_family_id, 0) + 1
                if edge_hits >= self.EDGE_PERSISTENCE_THRESHOLD:
                    return FamilyDecision(
                        status="FAMILY_EDGE",
                        family_id=None,
                        symbol_id=symbol_id,
                        confidence=0.4,
                        rationale=(f"Persistent borderline proximity ({edge_hits} hits) to {best_family_id} "
                                   f"at dist {min_dist:.3f}. Earned neutral EDGE status.")
                    )
                else:
                    return FamilyDecision(
                        status="FAMILY_HOLD",
                        family_id=best_family_id,
                        symbol_id=symbol_id,
                        confidence=0.2,
                        rationale=(f"Symbol {symbol_id} in borderline band (dist={min_dist:.3f}, {envelope_str} envelope) "
                                   f"for {best_family_id}. Hold for structural earning.")
                    )

        # 3. If no family match, it could be a NEW_FAMILY or NO_FAMILY_MATCH (isolated)
        # For v1, we require the symbol itself to be very stable to start a new family
        # (Assuming the caller only passes stable symbols here).
        return FamilyDecision(
            status="NEW_FAMILY",
            family_id=None,
            symbol_id=symbol_id,
            confidence=1.0,
            rationale=f"No existing structural family found within hold threshold ({self.HOLD_THRESHOLD})."
        )

    def join_or_create_family(self, symbol_id: str, signature: dict[str, float], spread: dict[str, float], hit_count: int) -> FamilyDecision:
        """
        Executes the family decision: either joins an existing family, mints a new one, 
        or holds if kinship is uncertain.
        """
        decision = self.evaluate_symbol(symbol_id, signature, spread)
        
        if decision.status == "JOIN_EXISTING_FAMILY":
            fam_id = decision.family_id
            if fam_id:
                record = self._families[fam_id]
                
                # Store member's structural signature and spread for internal analysis
                self._symbol_signatures[symbol_id] = signature.copy()
                self._symbol_spreads[symbol_id] = spread.copy()

                # Update combined signature (weighted moving average)
                # This now happens for BOTH new members and existing members
                new_count = record.observation_count + hit_count
                for axis in ["axis_a", "axis_b", "axis_c", "axis_d"]:
                    # Weighted average for centroid
                    current_val = record.current_signature.get(axis, 0.0)
                    new_val = signature.get(axis, 0.0)
                    avg_sig = (current_val * record.observation_count + new_val * hit_count) / new_count
                    record.current_signature[axis] = avg_sig
                    
                    # Weighted average for spread/envelope
                    current_spread_val = record.current_spread.get(axis, 0.0)
                    new_spread_val = spread.get(axis, 0.0)
                    avg_spread = (current_spread_val * record.observation_count + new_spread_val * hit_count) / new_count
                    record.current_spread[axis] = avg_spread
                
                record.observation_count = new_count
                
                # If it's a new member, add to membership list
                if symbol_id not in self._symbol_to_family:
                    record.member_symbol_ids.append(symbol_id)
                    self._symbol_to_family[symbol_id] = fam_id
                
                # Check for internal structural fracture/instability on every update
                self._check_for_fracture(fam_id)
                
                # Cleanup pending status
                if symbol_id in self._pending_kinship:
                    if fam_id in self._pending_kinship[symbol_id]:
                        del self._pending_kinship[symbol_id][fam_id]
                
        elif decision.status == "FAMILY_HOLD":
            # Track persistence in the hold band
            fam_id = decision.family_id
            if fam_id:
                if symbol_id not in self._pending_kinship:
                    self._pending_kinship[symbol_id] = {}
                
                # Check if it was specifically a boundary/edge hold
                if "borderline band" in decision.rationale:
                    if symbol_id not in self._pending_edge:
                        self._pending_edge[symbol_id] = {}
                    current_edge = self._pending_edge[symbol_id].get(fam_id, 0)
                    self._pending_edge[symbol_id][fam_id] = current_edge + 1
                else:
                    # Normal join persistence
                    current_hits = self._pending_kinship[symbol_id].get(fam_id, 0)
                    self._pending_kinship[symbol_id][fam_id] = current_hits + 1
                    
        elif decision.status == "FAMILY_TENSION":
            # Track persistence of multi-family tension
            current_tension = self._pending_bridge.get(symbol_id, 0)
            self._pending_bridge[symbol_id] = current_tension + 1
            
        elif decision.status == "FAMILY_BRIDGE" or decision.status == "FAMILY_EDGE":
            # Record persistent boundary status
            self._earned_boundary_statuses[symbol_id] = decision.status
            # We don't join a family or mint one yet, but we store the earned status
            
        elif decision.status == "NEW_FAMILY":
            self._family_counter += 1
            fam_id = f"fam_{self._family_counter:02d}"
            
            # Store member's structural signature and spread for internal analysis
            self._symbol_signatures[symbol_id] = signature.copy()
            self._symbol_spreads[symbol_id] = spread.copy()

            record = NeutralFamilyRecordV1(
                family_id=fam_id,
                member_symbol_ids=[symbol_id],
                mint_signature=signature.copy(),
                current_signature=signature.copy(),
                mint_spread=spread.copy(),
                current_spread=spread.copy(),
                observation_count=hit_count
            )
            self._families[fam_id] = record
            self._symbol_to_family[symbol_id] = fam_id
            decision.family_id = fam_id
            decision.rationale += f" Minted family {fam_id} with spread {spread}."

        # Evaluate pairwise family reunion opportunities after each structural update.
        self._check_for_reunion_candidates()

        return decision

    def get_family_for_symbol(self, symbol_id: str) -> Optional[str]:
        """Returns the family ID for a given symbol, if any."""
        return self._symbol_to_family.get(symbol_id)

    def get_family_record(self, family_id: str) -> Optional[NeutralFamilyRecordV1]:
        """Returns the full record for a given family ID."""
        return self._families.get(family_id)

    def get_fission_events(self) -> list[dict]:
        """Returns the full in-process fission event log."""
        return list(self._fission_events)

    def get_fission_events_for_family(self, family_id: str) -> list[dict]:
        """Returns fission events where the family was parent or successor."""
        out: list[dict] = []
        for evt in self._fission_events:
            if evt.get("parent_family_id") == family_id or family_id in evt.get("successor_family_ids", []):
                out.append(evt)
        return out

    def get_reunion_events(self) -> list[dict]:
        """Returns the full in-process reunion event log."""
        return list(self._reunion_events)

    def get_reunion_events_for_family(self, family_id: str) -> list[dict]:
        """Returns reunion events where the family was source or successor."""
        out: list[dict] = []
        for evt in self._reunion_events:
            if family_id in evt.get("source_family_ids", []) or evt.get("successor_family_id") == family_id:
                out.append(evt)
        return out

    def get_durable_ledger_path(self) -> str:
        """Returns the local file path used by the durable family-transition ledger."""
        return self._durable_ledger_path

    def get_event_ledger(self) -> list[dict]:
        """Reads and returns all durable ledger event records."""
        path = self._durable_ledger_path
        if not os.path.exists(path):
            return []
        events: list[dict] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                events.append(json.loads(line))
        return events

    def get_events_for_family(self, family_id: str) -> list[dict]:
        """
        Reads durable ledger and returns events where family_id appears as a
        source or successor family.
        """
        out: list[dict] = []
        for evt in self.get_event_ledger():
            sources = evt.get("source_family_ids", [])
            successors = evt.get("successor_family_ids", [])
            if family_id in sources or family_id in successors:
                out.append(evt)
        return out

    def _build_ancestry_index(self) -> dict:
        """
        Builds deterministic ancestry indices from the durable ledger.
        Durable ledger is treated as primary transition truth.
        """
        events = self.get_event_ledger()
        origin_event_by_family: dict[str, dict] = {}
        parent_family_ids_by_family: dict[str, list[str]] = {}
        successor_family_ids_by_family: dict[str, list[str]] = {}
        involved_events_by_family: dict[str, list[dict]] = {}

        for evt in events:
            source_ids = [str(x) for x in evt.get("source_family_ids", []) if str(x)]
            successor_ids = [str(x) for x in evt.get("successor_family_ids", []) if str(x)]

            for fam_id in set(source_ids + successor_ids):
                involved_events_by_family.setdefault(fam_id, []).append(evt)

            for succ_id in successor_ids:
                if succ_id not in origin_event_by_family:
                    origin_event_by_family[succ_id] = evt
                parent_family_ids_by_family.setdefault(succ_id, [])
                for src_id in source_ids:
                    if src_id not in parent_family_ids_by_family[succ_id]:
                        parent_family_ids_by_family[succ_id].append(src_id)

            for src_id in source_ids:
                successor_family_ids_by_family.setdefault(src_id, [])
                for succ_id in successor_ids:
                    if succ_id not in successor_family_ids_by_family[src_id]:
                        successor_family_ids_by_family[src_id].append(succ_id)

        return {
            "origin_event_by_family": origin_event_by_family,
            "parent_family_ids_by_family": parent_family_ids_by_family,
            "successor_family_ids_by_family": successor_family_ids_by_family,
            "involved_events_by_family": involved_events_by_family,
        }

    def _family_known_in_ledger_or_records(self, family_id: str, ancestry_index: dict) -> bool:
        if family_id in self._families:
            return True
        if family_id in ancestry_index["origin_event_by_family"]:
            return True
        if family_id in ancestry_index["parent_family_ids_by_family"]:
            return True
        if family_id in ancestry_index["successor_family_ids_by_family"]:
            return True
        if family_id in ancestry_index["involved_events_by_family"]:
            return True
        return False

    def get_family_origin(self, family_id: str) -> dict:
        """
        Returns the creating transition event for family_id when present in durable ledger.
        """
        idx = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, idx)
        evt = idx["origin_event_by_family"].get(family_id)
        if evt is None:
            return {
                "family_id": family_id,
                "found": False,
                "family_known": known,
                "origin_event_id": None,
                "origin_event_type": None,
                "parent_family_ids": [],
            }
        return {
            "family_id": family_id,
            "found": True,
            "family_known": True,
            "origin_event_id": evt.get("event_id"),
            "origin_event_type": evt.get("event_type"),
            "parent_family_ids": list(evt.get("source_family_ids", [])),
            "origin_event": evt,
        }

    def get_family_parents(self, family_id: str) -> dict:
        """
        Returns parent/source family IDs that produced family_id via transition event.
        """
        origin = self.get_family_origin(family_id)
        return {
            "family_id": family_id,
            "found": bool(origin["found"]),
            "family_known": bool(origin["family_known"]),
            "parent_family_ids": list(origin.get("parent_family_ids", [])),
            "origin_event_id": origin.get("origin_event_id"),
            "origin_event_type": origin.get("origin_event_type"),
        }

    def get_family_successors(self, family_id: str, recursive: bool = False, max_depth: int = 6) -> dict:
        """
        Returns successor family IDs for family_id from durable transition ledger.
        """
        if max_depth < 0:
            max_depth = 0
        idx = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, idx)
        direct = list(idx["successor_family_ids_by_family"].get(family_id, []))
        if not recursive:
            return {
                "family_id": family_id,
                "found": bool(direct),
                "family_known": known,
                "recursive": False,
                "max_depth": max_depth,
                "direct_successor_family_ids": direct,
                "descendant_family_ids": direct,
                "loop_detected": False,
                "truncated": False,
            }

        descendants: list[str] = []
        queue: list[tuple[str, int, set[str]]] = [(family_id, 0, {family_id})]
        visited_depth: dict[str, int] = {}
        loop_detected = False
        truncated = False

        while queue:
            current, depth, path = queue.pop(0)
            prev_depth = visited_depth.get(current)
            if prev_depth is not None and depth >= prev_depth:
                continue
            visited_depth[current] = depth
            if depth >= max_depth:
                if idx["successor_family_ids_by_family"].get(current):
                    truncated = True
                continue
            for succ in idx["successor_family_ids_by_family"].get(current, []):
                if succ not in descendants:
                    descendants.append(succ)
                if succ in path:
                    loop_detected = True
                    continue
                queue.append((succ, depth + 1, set(path) | {succ}))

        return {
            "family_id": family_id,
            "found": bool(descendants),
            "family_known": known,
            "recursive": True,
            "max_depth": max_depth,
            "direct_successor_family_ids": direct,
            "descendant_family_ids": descendants,
            "loop_detected": loop_detected,
            "truncated": truncated,
        }

    def get_family_transition_events(self, family_id: str) -> dict:
        """
        Returns durable transition events involving family_id.
        """
        idx = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, idx)
        events = list(idx["involved_events_by_family"].get(family_id, []))
        return {
            "family_id": family_id,
            "family_known": known,
            "event_count": len(events),
            "events": events,
        }

    def get_family_lineage(self, family_id: str, max_depth: int = 6) -> dict:
        """
        Returns a bounded, loop-safe ancestry chain (upward traversal by parent links).
        """
        if max_depth < 0:
            max_depth = 0
        idx = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, idx)
        if not known:
            return {
                "family_id": family_id,
                "family_known": False,
                "max_depth": max_depth,
                "lineage_nodes": [],
                "lineage_edges": [],
                "loop_detected": False,
                "truncated": False,
            }

        lineage_nodes: list[dict] = []
        lineage_edges: list[dict] = []
        queue: list[tuple[str, int, set[str]]] = [(family_id, 0, {family_id})]
        visited_depth: dict[str, int] = {}
        loop_detected = False
        truncated = False

        while queue:
            current, depth, path = queue.pop(0)
            prev_depth = visited_depth.get(current)
            if prev_depth is not None and depth >= prev_depth:
                continue
            visited_depth[current] = depth

            evt = idx["origin_event_by_family"].get(current)
            parents = list(idx["parent_family_ids_by_family"].get(current, []))
            lineage_nodes.append(
                {
                    "family_id": current,
                    "depth": depth,
                    "origin_event_id": evt.get("event_id") if evt else None,
                    "origin_event_type": evt.get("event_type") if evt else None,
                    "parent_family_ids": parents,
                }
            )

            if depth >= max_depth:
                if parents:
                    truncated = True
                continue

            for parent_id in parents:
                lineage_edges.append(
                    {
                        "child_family_id": current,
                        "parent_family_id": parent_id,
                        "event_id": evt.get("event_id") if evt else None,
                        "event_type": evt.get("event_type") if evt else None,
                    }
                )
                if parent_id in path:
                    loop_detected = True
                    continue
                queue.append((parent_id, depth + 1, set(path) | {parent_id}))

        return {
            "family_id": family_id,
            "family_known": True,
            "max_depth": max_depth,
            "lineage_nodes": lineage_nodes,
            "lineage_edges": lineage_edges,
            "loop_detected": loop_detected,
            "truncated": truncated,
        }

    def _collect_ancestor_ids(self, family_id: str, max_depth: int, ancestry_index: dict) -> tuple[set[str], bool, bool]:
        """
        Collects ancestor IDs (including family_id) with depth bound and loop guard.
        Returns: (ancestor_ids, loop_detected, truncated)
        """
        ancestors: set[str] = set()
        queue: list[tuple[str, int, set[str]]] = [(family_id, 0, {family_id})]
        visited_depth: dict[str, int] = {}
        loop_detected = False
        truncated = False

        while queue:
            current, depth, path = queue.pop(0)
            prev_depth = visited_depth.get(current)
            if prev_depth is not None and depth >= prev_depth:
                continue
            visited_depth[current] = depth
            ancestors.add(current)

            parents = ancestry_index["parent_family_ids_by_family"].get(current, [])
            if depth >= max_depth:
                if parents:
                    truncated = True
                continue
            for parent_id in parents:
                if parent_id in path:
                    loop_detected = True
                    continue
                queue.append((parent_id, depth + 1, set(path) | {parent_id}))

        return ancestors, loop_detected, truncated

    def families_share_ancestry(self, family_a: str, family_b: str, max_depth: int = 6) -> dict:
        """
        Checks whether two families share any ancestor within max_depth traversal.
        """
        if max_depth < 0:
            max_depth = 0
        idx = self._build_ancestry_index()
        known_a = self._family_known_in_ledger_or_records(family_a, idx)
        known_b = self._family_known_in_ledger_or_records(family_b, idx)
        if not known_a or not known_b:
            return {
                "family_a": family_a,
                "family_b": family_b,
                "max_depth": max_depth,
                "family_a_known": known_a,
                "family_b_known": known_b,
                "shares_ancestry": False,
                "shared_ancestor_ids": [],
                "loop_detected": False,
                "truncated": False,
            }

        anc_a, loop_a, trunc_a = self._collect_ancestor_ids(family_a, max_depth, idx)
        anc_b, loop_b, trunc_b = self._collect_ancestor_ids(family_b, max_depth, idx)
        shared = sorted(anc_a.intersection(anc_b))
        return {
            "family_a": family_a,
            "family_b": family_b,
            "max_depth": max_depth,
            "family_a_known": True,
            "family_b_known": True,
            "shares_ancestry": len(shared) > 0,
            "shared_ancestor_ids": shared,
            "family_a_ancestor_ids": sorted(anc_a),
            "family_b_ancestor_ids": sorted(anc_b),
            "loop_detected": bool(loop_a or loop_b),
            "truncated": bool(trunc_a or trunc_b),
        }

    def _extract_issue_family_ids(self, issue: dict) -> list[str]:
        ids: list[str] = []
        for key in [
            "family_id",
            "source_family_id",
            "successor_family_id",
            "parent_family_id",
        ]:
            val = issue.get(key)
            if isinstance(val, str) and val:
                ids.append(val)
        for key in [
            "family_ids",
            "source_family_ids",
            "successor_family_ids",
            "parent_family_ids",
        ]:
            val = issue.get(key, [])
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, str) and item:
                        ids.append(item)
        return sorted(set(ids))

    def run_lineage_integrity_audit(self, family_id: Optional[str] = None, max_depth: int = 8) -> dict:
        """
        Runs a structural lineage integrity audit over current family records and durable ledger.

        Categories:
        - record_issues
        - ledger_issues
        - cross_source_issues
        """
        if max_depth < 0:
            max_depth = 0

        record_issues: list[dict] = []
        ledger_issues: list[dict] = []
        cross_source_issues: list[dict] = []

        events = self.get_event_ledger()
        record_family_ids = sorted(self._families.keys())
        record_family_set = set(record_family_ids)

        # ---- Ledger-level checks ----
        event_id_counts: dict[str, int] = {}
        for evt in events:
            evt_id = str(evt.get("event_id", ""))
            if evt_id:
                event_id_counts[evt_id] = event_id_counts.get(evt_id, 0) + 1
            else:
                ledger_issues.append(
                    {
                        "issue_type": "LEDGER_EVENT_MISSING_EVENT_ID",
                        "event_id": None,
                        "details": {"event_record": evt},
                    }
                )

        for evt_id in sorted(event_id_counts.keys()):
            count = event_id_counts[evt_id]
            if count > 1:
                ledger_issues.append(
                    {
                        "issue_type": "LEDGER_DUPLICATE_EVENT_ID",
                        "event_id": evt_id,
                        "details": {"duplicate_count": count},
                    }
                )

        for evt in events:
            evt_id = str(evt.get("event_id", ""))
            src_ids = evt.get("source_family_ids", [])
            succ_ids = evt.get("successor_family_ids", [])
            if not isinstance(src_ids, list):
                ledger_issues.append(
                    {
                        "issue_type": "LEDGER_EVENT_INVALID_SOURCE_FAMILY_IDS_TYPE",
                        "event_id": evt_id,
                        "details": {"source_family_ids_type": str(type(src_ids))},
                    }
                )
                src_ids = []
            if not isinstance(succ_ids, list):
                ledger_issues.append(
                    {
                        "issue_type": "LEDGER_EVENT_INVALID_SUCCESSOR_FAMILY_IDS_TYPE",
                        "event_id": evt_id,
                        "details": {"successor_family_ids_type": str(type(succ_ids))},
                    }
                )
                succ_ids = []

            for fam in src_ids:
                if not isinstance(fam, str) or not fam:
                    ledger_issues.append(
                        {
                            "issue_type": "LEDGER_EVENT_INVALID_SOURCE_FAMILY_ID",
                            "event_id": evt_id,
                            "source_family_id": fam,
                            "details": {},
                        }
                    )
            for fam in succ_ids:
                if not isinstance(fam, str) or not fam:
                    ledger_issues.append(
                        {
                            "issue_type": "LEDGER_EVENT_INVALID_SUCCESSOR_FAMILY_ID",
                            "event_id": evt_id,
                            "successor_family_id": fam,
                            "details": {},
                        }
                    )

        # ---- Record-level checks ----
        for fam_id in record_family_ids:
            rec = self._families[fam_id]
            is_active = rec.lifecycle_status == "FAMILY_ACTIVE"
            if not is_active and rec.member_symbol_ids:
                record_issues.append(
                    {
                        "issue_type": "INACTIVE_FAMILY_HAS_ACTIVE_MEMBERS",
                        "family_id": fam_id,
                        "details": {
                            "lifecycle_status": rec.lifecycle_status,
                            "member_symbol_ids": list(rec.member_symbol_ids),
                        },
                    }
                )

            for succ_id in rec.lineage_successor_family_ids:
                if succ_id not in record_family_set:
                    record_issues.append(
                        {
                            "issue_type": "FAMILY_RECORD_UNKNOWN_SUCCESSOR_REFERENCE",
                            "family_id": fam_id,
                            "successor_family_id": succ_id,
                            "details": {},
                        }
                    )

        # One-family-only and mapping consistency checks.
        symbol_memberships: dict[str, list[str]] = {}
        for fam_id in record_family_ids:
            rec = self._families[fam_id]
            for sym_id in rec.member_symbol_ids:
                symbol_memberships.setdefault(sym_id, []).append(fam_id)

        for sym_id in sorted(symbol_memberships.keys()):
            fams = sorted(symbol_memberships[sym_id])
            if len(fams) > 1:
                record_issues.append(
                    {
                        "issue_type": "SYMBOL_MULTI_FAMILY_MEMBERSHIP_VIOLATION",
                        "symbol_id": sym_id,
                        "family_ids": fams,
                        "details": {},
                    }
                )
            mapped = self._symbol_to_family.get(sym_id)
            if mapped is None:
                record_issues.append(
                    {
                        "issue_type": "SYMBOL_MISSING_SYMBOL_TO_FAMILY_MAPPING",
                        "symbol_id": sym_id,
                        "family_ids": fams,
                        "details": {},
                    }
                )
            elif mapped not in fams:
                record_issues.append(
                    {
                        "issue_type": "SYMBOL_MAPPING_MEMBERSHIP_MISMATCH",
                        "symbol_id": sym_id,
                        "family_ids": fams,
                        "mapped_family_id": mapped,
                        "details": {},
                    }
                )

        for sym_id in sorted(self._symbol_to_family.keys()):
            fam = self._symbol_to_family[sym_id]
            if fam not in record_family_set:
                record_issues.append(
                    {
                        "issue_type": "SYMBOL_MAPPING_REFERENCES_UNKNOWN_FAMILY",
                        "symbol_id": sym_id,
                        "family_id": fam,
                        "details": {},
                    }
                )

        # ---- Cross-source checks (ledger <-> records) ----
        for evt in events:
            evt_id = str(evt.get("event_id", ""))
            evt_type = str(evt.get("event_type", ""))
            src_ids = [x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x]
            succ_ids = [x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x]

            for fam in src_ids + succ_ids:
                if fam not in record_family_set:
                    cross_source_issues.append(
                        {
                            "issue_type": "LEDGER_REFERENCES_UNKNOWN_FAMILY_IN_RECORDS",
                            "event_id": evt_id,
                            "family_id": fam,
                            "details": {"event_type": evt_type},
                        }
                    )

            for succ_id in succ_ids:
                succ_rec = self._families.get(succ_id)
                if not succ_rec:
                    continue
                if evt_type == "FAMILY_FISSION_V1":
                    expected_parents = sorted(src_ids)
                    actual_parents = sorted([succ_rec.lineage_parent_family_id] if succ_rec.lineage_parent_family_id else [])
                    if expected_parents != actual_parents:
                        cross_source_issues.append(
                            {
                                "issue_type": "SUCCESSOR_PARENT_LINEAGE_MISMATCH",
                                "event_id": evt_id,
                                "family_id": succ_id,
                                "details": {
                                    "event_type": evt_type,
                                    "expected_parent_family_ids": expected_parents,
                                    "record_parent_family_ids": actual_parents,
                                },
                            }
                        )
                    if succ_rec.lineage_fission_event_id != evt_id:
                        cross_source_issues.append(
                            {
                                "issue_type": "SUCCESSOR_ORIGIN_EVENT_MISMATCH",
                                "event_id": evt_id,
                                "family_id": succ_id,
                                "details": {
                                    "event_type": evt_type,
                                    "expected_origin_event_id": evt_id,
                                    "record_origin_event_id": succ_rec.lineage_fission_event_id,
                                },
                            }
                        )
                if evt_type == "FAMILY_REUNION_V1":
                    expected_parents = sorted(src_ids)
                    actual_parents = sorted(succ_rec.lineage_parent_family_ids)
                    if expected_parents != actual_parents:
                        cross_source_issues.append(
                            {
                                "issue_type": "SUCCESSOR_PARENT_LINEAGE_MISMATCH",
                                "event_id": evt_id,
                                "family_id": succ_id,
                                "details": {
                                    "event_type": evt_type,
                                    "expected_parent_family_ids": expected_parents,
                                    "record_parent_family_ids": actual_parents,
                                },
                            }
                        )
                    if succ_rec.lineage_reunion_event_id != evt_id:
                        cross_source_issues.append(
                            {
                                "issue_type": "SUCCESSOR_ORIGIN_EVENT_MISMATCH",
                                "event_id": evt_id,
                                "family_id": succ_id,
                                "details": {
                                    "event_type": evt_type,
                                    "expected_origin_event_id": evt_id,
                                    "record_origin_event_id": succ_rec.lineage_reunion_event_id,
                                },
                            }
                        )

            for src_id in src_ids:
                src_rec = self._families.get(src_id)
                if not src_rec:
                    continue
                expected_succ = sorted(succ_ids)
                actual_succ = sorted(src_rec.lineage_successor_family_ids)
                if not all(s in actual_succ for s in expected_succ):
                    cross_source_issues.append(
                        {
                            "issue_type": "SOURCE_SUCCESSOR_LINEAGE_MISMATCH",
                            "event_id": evt_id,
                            "family_id": src_id,
                            "details": {
                                "event_type": evt_type,
                                "expected_successor_family_ids": expected_succ,
                                "record_successor_family_ids": actual_succ,
                            },
                        }
                    )

        # ---- Loop checks (bounded + explicit) ----
        loop_issues: list[dict] = []
        succ_graph: dict[str, list[str]] = {}
        for evt in events:
            src_ids = [x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x]
            succ_ids = [x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x]
            for src in src_ids:
                succ_graph.setdefault(src, [])
                for succ in succ_ids:
                    if succ not in succ_graph[src]:
                        succ_graph[src].append(succ)
            for fam in src_ids + succ_ids:
                succ_graph.setdefault(fam, [])

        # Deterministic DFS with path-based cycle detection and depth bound.
        for root in sorted(succ_graph.keys()):
            stack: list[tuple[str, int, list[str]]] = [(root, 0, [root])]
            while stack:
                node, depth, path = stack.pop()
                if depth >= max_depth:
                    continue
                for nxt in sorted(succ_graph.get(node, [])):
                    if nxt in path:
                        loop_issues.append(
                            {
                                "issue_type": "LINEAGE_LOOP_DETECTED",
                                "family_id": root,
                                "family_ids": path + [nxt],
                                "details": {"max_depth": max_depth},
                            }
                        )
                        continue
                    stack.append((nxt, depth + 1, path + [nxt]))

        # Deduplicate loop issues by path key for deterministic report size.
        dedup_loop: dict[str, dict] = {}
        for issue in loop_issues:
            key = "|".join(issue.get("family_ids", []))
            if key not in dedup_loop:
                dedup_loop[key] = issue
        loop_issues = [dedup_loop[k] for k in sorted(dedup_loop.keys())]

        # place loop issues under cross-source category for separation contract
        cross_source_issues.extend(loop_issues)

        # Optional per-family filtering
        family_known = True
        if family_id is not None:
            idx = self._build_ancestry_index()
            family_known = self._family_known_in_ledger_or_records(family_id, idx)

            def _matches(issue: dict) -> bool:
                return family_id in self._extract_issue_family_ids(issue)

            record_issues = [i for i in record_issues if _matches(i)]
            ledger_issues = [i for i in ledger_issues if _matches(i)]
            cross_source_issues = [i for i in cross_source_issues if _matches(i)]

        issue_count = len(record_issues) + len(ledger_issues) + len(cross_source_issues)
        report = {
            "ok": issue_count == 0,
            "issue_count": issue_count,
            "checked_family_id": family_id,
            "family_known": family_known if family_id is not None else None,
            "max_depth": max_depth,
            "record_issues": record_issues,
            "ledger_issues": ledger_issues,
            "cross_source_issues": cross_source_issues,
            "issue_counts_by_category": {
                "record_issues": len(record_issues),
                "ledger_issues": len(ledger_issues),
                "cross_source_issues": len(cross_source_issues),
            },
        }
        return report

    def get_lineage_integrity_report(self, family_id: Optional[str] = None, max_depth: int = 8) -> dict:
        """Alias for run_lineage_integrity_audit for query-style usage."""
        return self.run_lineage_integrity_audit(family_id=family_id, max_depth=max_depth)

    def get_family_dossier(self, family_id: str, max_depth: int = 8) -> dict:
        """
        Returns a compact, structured family dossier assembled from current records,
        durable ledger, ancestry queries, and per-family lineage integrity audit.
        """
        if max_depth < 0:
            max_depth = 0

        ancestry_index = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, ancestry_index)
        if not known:
            return {
                "family_id": family_id,
                "found": False,
                "max_depth": max_depth,
                "reason": "FAMILY_NOT_FOUND",
                "identity": None,
                "origin_lineage": None,
                "descendants": None,
                "event_history": [],
                "relations": None,
                "integrity_summary": None,
                "geometry_fit_summary": None,
                "topology_summary": None,
            }

        rec = self._families.get(family_id)
        identity = {
            "family_id": family_id,
            "record_present": rec is not None,
            "lifecycle_status": rec.lifecycle_status if rec else None,
            "current_member_symbol_ids": sorted(list(rec.member_symbol_ids)) if rec else [],
            "historical_member_symbol_ids": sorted(list(rec.historical_member_symbol_ids)) if rec else [],
            "mint_signature": dict(rec.mint_signature) if rec else None,
            "current_signature": dict(rec.current_signature) if rec else None,
            "mint_spread": dict(rec.mint_spread) if rec else None,
            "current_spread": dict(rec.current_spread) if rec else None,
            "lineage_parent_family_id": rec.lineage_parent_family_id if rec else None,
            "lineage_parent_family_ids": sorted(list(rec.lineage_parent_family_ids)) if rec else [],
            "lineage_successor_family_ids": sorted(list(rec.lineage_successor_family_ids)) if rec else [],
        }

        origin = self.get_family_origin(family_id)
        lineage = self.get_family_lineage(family_id, max_depth=max_depth)
        origin_lineage = {
            "origin": origin,
            "lineage_chain": lineage,
        }

        successors_recursive = self.get_family_successors(
            family_id=family_id, recursive=True, max_depth=max_depth
        )
        descendants = {
            "direct_successor_family_ids": list(successors_recursive.get("direct_successor_family_ids", [])),
            "descendant_family_ids": list(successors_recursive.get("descendant_family_ids", [])),
            "recursive": True,
            "max_depth": max_depth,
            "loop_detected": bool(successors_recursive.get("loop_detected", False)),
            "truncated": bool(successors_recursive.get("truncated", False)),
        }

        events = list(self.get_events_for_family(family_id))
        events.sort(
            key=lambda e: (
                int(e.get("event_order", 10**9)),
                int(e.get("ledger_write_order", 10**9)),
                str(e.get("event_id", "")),
            )
        )
        event_history = {
            "event_count": len(events),
            "events": events,
        }

        related_candidates = sorted(
            set(origin.get("parent_family_ids", [])) |
            set(descendants.get("direct_successor_family_ids", []))
        )
        shared_ancestry_with_related: list[dict] = []
        for other_id in related_candidates:
            shared_ancestry_with_related.append(
                self.families_share_ancestry(family_id, other_id, max_depth=max_depth)
            )
        relations = {
            "immediate_related_family_ids": related_candidates,
            "shared_ancestry_with_immediate_related": shared_ancestry_with_related,
        }

        integrity = self.run_lineage_integrity_audit(family_id=family_id, max_depth=max_depth)
        integrity_summary = {
            "ok": bool(integrity.get("ok", False)),
            "issue_count": int(integrity.get("issue_count", 0)),
            "issue_counts_by_category": dict(integrity.get("issue_counts_by_category", {})),
            "record_issues": list(integrity.get("record_issues", [])),
            "ledger_issues": list(integrity.get("ledger_issues", [])),
            "cross_source_issues": list(integrity.get("cross_source_issues", [])),
        }

        return {
            "family_id": family_id,
            "found": True,
            "max_depth": max_depth,
            "identity": identity,
            "origin_lineage": origin_lineage,
            "descendants": descendants,
            "event_history": event_history,
            "relations": relations,
            "integrity_summary": integrity_summary,
            "geometry_fit_summary": self.get_family_geometry_fit(family_id),
            "topology_summary": self.get_family_topology_audit(family_id),
        }

    def get_family_ancestry_report(self, family_id: str, max_depth: int = 8) -> dict:
        """Alias for get_family_dossier for report-style usage."""
        return self.get_family_dossier(family_id=family_id, max_depth=max_depth)

    def _get_ledger_event_by_id(self, event_id: str) -> tuple[Optional[dict], int]:
        """
        Returns (event_record, duplicate_count) for event_id from durable ledger.
        event_record is the first ledger occurrence in read order, or None if missing.
        """
        found_event: Optional[dict] = None
        duplicate_count = 0
        for evt in self.get_event_ledger():
            if str(evt.get("event_id", "")) == event_id:
                duplicate_count += 1
                if found_event is None:
                    found_event = evt
        return found_event, duplicate_count

    def _build_family_state_snapshot(self, family_id: str) -> dict:
        """Returns a deterministic current-state snapshot for one family record."""
        rec = self._families.get(family_id)
        if rec is None:
            return {
                "family_id": family_id,
                "record_present": False,
                "lifecycle_status": None,
                "current_member_symbol_ids": [],
                "historical_member_symbol_ids": [],
                "current_member_count": 0,
                "historical_member_count": 0,
                "mint_signature": None,
                "current_signature": None,
                "mint_spread": None,
                "current_spread": None,
            }
        current_ids = sorted(list(rec.member_symbol_ids))
        historical_ids = sorted(list(rec.historical_member_symbol_ids))
        return {
            "family_id": family_id,
            "record_present": True,
            "lifecycle_status": rec.lifecycle_status,
            "current_member_symbol_ids": current_ids,
            "historical_member_symbol_ids": historical_ids,
            "current_member_count": len(current_ids),
            "historical_member_count": len(historical_ids),
            "mint_signature": dict(rec.mint_signature),
            "current_signature": dict(rec.current_signature),
            "mint_spread": dict(rec.mint_spread),
            "current_spread": dict(rec.current_spread),
        }

    def _build_event_member_summary(self, event_record: dict) -> dict:
        """
        Returns normalized member/partition summary from stored event fields only.
        Does not fabricate historical snapshots.
        """
        partition = event_record.get("partition")
        members = event_record.get("members")
        summary = {
            "partition": partition if isinstance(partition, dict) else None,
            "members": members if isinstance(members, dict) else None,
            "member_id_count": 0,
            "member_ids": [],
            "source_member_counts": {},
            "successor_member_counts": {},
        }

        member_ids: set[str] = set()
        if isinstance(partition, dict):
            g1 = [x for x in partition.get("group_1_member_ids", []) if isinstance(x, str) and x]
            g2 = [x for x in partition.get("group_2_member_ids", []) if isinstance(x, str) and x]
            member_ids.update(g1)
            member_ids.update(g2)
            source_ids = [x for x in event_record.get("source_family_ids", []) if isinstance(x, str) and x]
            succ_ids = [x for x in event_record.get("successor_family_ids", []) if isinstance(x, str) and x]
            if source_ids:
                summary["source_member_counts"][source_ids[0]] = len(member_ids)
            if succ_ids:
                if len(succ_ids) >= 1:
                    summary["successor_member_counts"][succ_ids[0]] = len(g1)
                if len(succ_ids) >= 2:
                    summary["successor_member_counts"][succ_ids[1]] = len(g2)

        if isinstance(members, dict):
            source_a = [x for x in members.get("source_a_member_ids", []) if isinstance(x, str) and x]
            source_b = [x for x in members.get("source_b_member_ids", []) if isinstance(x, str) and x]
            reunited = [x for x in members.get("reunited_member_ids", []) if isinstance(x, str) and x]
            member_ids.update(source_a)
            member_ids.update(source_b)
            member_ids.update(reunited)

            source_ids = [x for x in event_record.get("source_family_ids", []) if isinstance(x, str) and x]
            succ_ids = [x for x in event_record.get("successor_family_ids", []) if isinstance(x, str) and x]
            if len(source_ids) >= 1:
                summary["source_member_counts"][source_ids[0]] = len(source_a)
            if len(source_ids) >= 2:
                summary["source_member_counts"][source_ids[1]] = len(source_b)
            if len(succ_ids) >= 1:
                summary["successor_member_counts"][succ_ids[0]] = len(reunited)

        summary["member_ids"] = sorted(member_ids)
        summary["member_id_count"] = len(summary["member_ids"])
        return summary

    def _build_event_scoped_integrity_summary(self, event_id: str, involved_family_ids: list[str], max_depth: int) -> dict:
        """
        Filters full lineage audit into an event-centered integrity view.
        Scope rule:
        - include issues explicitly tied to event_id, OR
        - include issues tied to directly involved family IDs.
        """
        full_report = self.run_lineage_integrity_audit(max_depth=max_depth)
        involved_set = set(involved_family_ids)

        def _matches(issue: dict) -> bool:
            if issue.get("event_id") == event_id:
                return True
            issue_family_ids = self._extract_issue_family_ids(issue)
            for fam_id in issue_family_ids:
                if fam_id in involved_set:
                    return True
            return False

        def _sort_issues(issues: list[dict]) -> list[dict]:
            return sorted(
                issues,
                key=lambda issue: (
                    str(issue.get("issue_type", "")),
                    str(issue.get("event_id", "")),
                    json.dumps(issue, sort_keys=True, separators=(",", ":")),
                ),
            )

        record_issues = _sort_issues([x for x in full_report.get("record_issues", []) if _matches(x)])
        ledger_issues = _sort_issues([x for x in full_report.get("ledger_issues", []) if _matches(x)])
        cross_source_issues = _sort_issues([x for x in full_report.get("cross_source_issues", []) if _matches(x)])
        issue_count = len(record_issues) + len(ledger_issues) + len(cross_source_issues)
        return {
            "scope": "EVENT_SCOPED",
            "event_id": event_id,
            "involved_family_ids": sorted(involved_set),
            "ok": issue_count == 0,
            "issue_count": issue_count,
            "issue_counts_by_category": {
                "record_issues": len(record_issues),
                "ledger_issues": len(ledger_issues),
                "cross_source_issues": len(cross_source_issues),
            },
            "record_issues": record_issues,
            "ledger_issues": ledger_issues,
            "cross_source_issues": cross_source_issues,
        }

    def _mean_distance_to_signature(self, member_ids: list[str], center_signature: dict[str, float]) -> float:
        """Average distance from member signatures to a center signature."""
        if not member_ids:
            return 0.0
        total = 0.0
        count = 0
        for m_id in member_ids:
            sig = self._symbol_signatures.get(m_id)
            if sig is None:
                continue
            total += self._calculate_distance(sig, center_signature)
            count += 1
        if count == 0:
            return 0.0
        return total / float(count)

    def _family_member_ids_for_fit(self, rec: NeutralFamilyRecordV1) -> tuple[list[str], str]:
        """
        Returns member IDs + basis used for geometry-fit evaluation.
        Uses current members when present, otherwise historical members.
        """
        current_ids = [x for x in rec.member_symbol_ids if isinstance(x, str) and x]
        if current_ids:
            return sorted(current_ids), "CURRENT_MEMBERS"
        historical_ids = [x for x in rec.historical_member_symbol_ids if isinstance(x, str) and x]
        if historical_ids:
            return sorted(historical_ids), "HISTORICAL_MEMBERS"
        return [], "NO_MEMBERS"

    def _compute_axis_variance(self, member_ids: list[str]) -> dict[str, float]:
        """Per-axis variance over member signatures."""
        axes = ["axis_a", "axis_b", "axis_c", "axis_d"]
        if not member_ids:
            return {axis: 0.0 for axis in axes}
        means = {axis: 0.0 for axis in axes}
        count = 0
        for m_id in member_ids:
            sig = self._symbol_signatures.get(m_id)
            if sig is None:
                continue
            count += 1
            for axis in axes:
                means[axis] += float(sig.get(axis, 0.0))
        if count == 0:
            return {axis: 0.0 for axis in axes}
        for axis in axes:
            means[axis] /= float(count)

        variances = {axis: 0.0 for axis in axes}
        for m_id in member_ids:
            sig = self._symbol_signatures.get(m_id)
            if sig is None:
                continue
            for axis in axes:
                diff = float(sig.get(axis, 0.0)) - means[axis]
                variances[axis] += diff * diff
        for axis in axes:
            variances[axis] /= float(count)
        return variances

    def _compute_pairwise_distance_metrics(self, member_ids: list[str]) -> dict:
        """Pairwise distance summary for member signatures."""
        distances: list[float] = []
        for i in range(len(member_ids)):
            sig_i = self._symbol_signatures.get(member_ids[i])
            if sig_i is None:
                continue
            for j in range(i + 1, len(member_ids)):
                sig_j = self._symbol_signatures.get(member_ids[j])
                if sig_j is None:
                    continue
                distances.append(self._calculate_distance(sig_i, sig_j))

        if not distances:
            return {
                "pair_count": 0,
                "mean_pairwise_distance": 0.0,
                "max_pairwise_distance": 0.0,
                "min_pairwise_distance": 0.0,
                "pairwise_distance_ratio": 0.0,
            }

        mean_d = sum(distances) / float(len(distances))
        max_d = max(distances)
        min_d = min(distances)
        return {
            "pair_count": len(distances),
            "mean_pairwise_distance": mean_d,
            "max_pairwise_distance": max_d,
            "min_pairwise_distance": min_d,
            "pairwise_distance_ratio": (max_d / max(mean_d, 1e-6)),
        }

    def get_family_topology_audit(self, family_id: str) -> dict:
        """
        Returns a first-pass structural shape audit for family member arrangement.
        This is separate from center/spread fit and focuses on topology compression risk.
        """
        ancestry_index = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, ancestry_index)
        if not known:
            return {
                "family_id": family_id,
                "found": False,
                "reason": "FAMILY_NOT_FOUND",
                "topology_available": False,
                "shape_class": "SHAPE_UNKNOWN",
                "compression_risk": False,
                "topology_warnings": [],
            }

        rec = self._families.get(family_id)
        if rec is None:
            return {
                "family_id": family_id,
                "found": True,
                "reason": "FAMILY_RECORD_NOT_AVAILABLE",
                "topology_available": False,
                "shape_class": "SHAPE_UNKNOWN",
                "compression_risk": False,
                "topology_warnings": [],
            }

        member_ids, member_basis = self._family_member_ids_for_fit(rec)
        if len(member_ids) < self.TOPOLOGY_MIN_MEMBERS:
            return {
                "family_id": family_id,
                "found": True,
                "topology_available": False,
                "shape_class": "SHAPE_UNKNOWN",
                "compression_risk": False,
                "topology_warnings": [],
                "reason": "INSUFFICIENT_MEMBER_GEOMETRY_FOR_TOPOLOGY",
                "member_basis": member_basis,
                "member_symbol_ids_used": member_ids,
                "member_count_used": len(member_ids),
                "topology_thresholds": {
                    "topology_min_members": int(self.TOPOLOGY_MIN_MEMBERS),
                    "compact_anisotropy_max": float(self.TOPOLOGY_COMPACT_ANISOTROPY_MAX),
                    "compact_pairwise_ratio_max": float(self.TOPOLOGY_COMPACT_PAIRWISE_RATIO_MAX),
                    "elongated_anisotropy_min": float(self.TOPOLOGY_ELONGATED_ANISOTROPY_MIN),
                    "elongated_pairwise_ratio_min": float(self.TOPOLOGY_ELONGATED_PAIRWISE_RATIO_MIN),
                },
            }

        missing_signature_ids = [m_id for m_id in member_ids if m_id not in self._symbol_signatures]
        if missing_signature_ids:
            return {
                "family_id": family_id,
                "found": True,
                "topology_available": False,
                "shape_class": "SHAPE_UNKNOWN",
                "compression_risk": False,
                "topology_warnings": ["FAMILY_TOPOLOGY_INPUT_INCOMPLETE"],
                "reason": "MEMBER_SIGNATURES_MISSING",
                "member_basis": member_basis,
                "member_symbol_ids_used": member_ids,
                "missing_signature_symbol_ids": sorted(missing_signature_ids),
            }

        axis_variance = self._compute_axis_variance(member_ids)
        variance_values = [float(axis_variance[a]) for a in ["axis_a", "axis_b", "axis_c", "axis_d"]]
        max_var = max(variance_values) if variance_values else 0.0
        min_var = min(variance_values) if variance_values else 0.0
        anisotropy_ratio = max_var / max(min_var, 1e-6)

        pairwise = self._compute_pairwise_distance_metrics(member_ids)
        pairwise_ratio = float(pairwise["pairwise_distance_ratio"])

        subgroup_partition = self._compute_subgroup_partition_from_member_ids(member_ids)
        subgroup_detected = subgroup_partition is not None
        subgroup_sizes = []
        if subgroup_partition is not None:
            subgroup_sizes = sorted([len(subgroup_partition[0]), len(subgroup_partition[1])])

        elongated_by_distance = (
            pairwise_ratio >= self.TOPOLOGY_ELONGATED_PAIRWISE_RATIO_MIN
            and float(pairwise["max_pairwise_distance"]) >= self.SUBGROUP_SEPARATION_THRESHOLD
        )
        shape_class = "SHAPE_UNKNOWN"
        if subgroup_detected:
            shape_class = "SHAPE_DUAL_LOBE"
        elif anisotropy_ratio >= self.TOPOLOGY_ELONGATED_ANISOTROPY_MIN or elongated_by_distance:
            shape_class = "SHAPE_ELONGATED"
        elif (
            anisotropy_ratio <= self.TOPOLOGY_COMPACT_ANISOTROPY_MAX
            and pairwise_ratio <= self.TOPOLOGY_COMPACT_PAIRWISE_RATIO_MAX
        ):
            shape_class = "SHAPE_COMPACT"

        compression_risk = shape_class in {"SHAPE_ELONGATED", "SHAPE_DUAL_LOBE"}
        topology_warnings: list[str] = []
        if compression_risk:
            topology_warnings.append("TOPOLOGY_COMPRESSION_RISK")
            topology_warnings.append("SHAPE_NOT_WELL_CAPTURED_BY_CENTER_SPREAD")

        return {
            "family_id": family_id,
            "found": True,
            "topology_available": True,
            "shape_class": shape_class,
            "compression_risk": compression_risk,
            "topology_warnings": sorted(set(topology_warnings)),
            "member_basis": member_basis,
            "member_symbol_ids_used": member_ids,
            "member_count_used": len(member_ids),
            "topology_metrics": {
                "axis_variance": axis_variance,
                "anisotropy_ratio": anisotropy_ratio,
                "pair_count": int(pairwise["pair_count"]),
                "mean_pairwise_distance": float(pairwise["mean_pairwise_distance"]),
                "max_pairwise_distance": float(pairwise["max_pairwise_distance"]),
                "min_pairwise_distance": float(pairwise["min_pairwise_distance"]),
                "pairwise_distance_ratio": pairwise_ratio,
                "subgroup_detected": subgroup_detected,
                "subgroup_count_estimate": 2 if subgroup_detected else 1,
                "subgroup_partition_sizes": subgroup_sizes,
            },
            "topology_thresholds": {
                "topology_min_members": int(self.TOPOLOGY_MIN_MEMBERS),
                "compact_anisotropy_max": float(self.TOPOLOGY_COMPACT_ANISOTROPY_MAX),
                "compact_pairwise_ratio_max": float(self.TOPOLOGY_COMPACT_PAIRWISE_RATIO_MAX),
                "elongated_anisotropy_min": float(self.TOPOLOGY_ELONGATED_ANISOTROPY_MIN),
                "elongated_pairwise_ratio_min": float(self.TOPOLOGY_ELONGATED_PAIRWISE_RATIO_MIN),
            },
        }

    def get_family_pressure_forecast(self, family_id: str) -> dict:
        """
        Returns a neutral structural pressure forecast for one family.

        Diagnostic-only:
        - no event creation
        - no lineage mutation
        - no probability claims
        """
        thresholds = {
            "subgroup_persistence_threshold": int(self.SUBGROUP_PERSISTENCE_THRESHOLD),
            "fracture_persistence_threshold": int(self.FRACTURE_PERSISTENCE_THRESHOLD),
            "fission_persistence_threshold": int(self.FISSION_PERSISTENCE_THRESHOLD),
            "topology_compact_anisotropy_max": float(self.TOPOLOGY_COMPACT_ANISOTROPY_MAX),
            "topology_compact_pairwise_ratio_max": float(self.TOPOLOGY_COMPACT_PAIRWISE_RATIO_MAX),
            "topology_elongated_anisotropy_min": float(self.TOPOLOGY_ELONGATED_ANISOTROPY_MIN),
            "topology_elongated_pairwise_ratio_min": float(self.TOPOLOGY_ELONGATED_PAIRWISE_RATIO_MIN),
            "pressure_stretched_threshold": float(self.PRESSURE_STRETCHED_THRESHOLD),
            "pressure_dual_center_threshold": float(self.PRESSURE_DUAL_CENTER_THRESHOLD),
            "pressure_instability_threshold": float(self.PRESSURE_INSTABILITY_THRESHOLD),
            "pressure_fission_prone_threshold": float(self.PRESSURE_FISSION_PRONE_THRESHOLD),
            "pressure_stable_threshold": float(self.PRESSURE_STABLE_THRESHOLD),
        }
        threshold_summary = {
            "thresholds": thresholds,
            "thresholds_provisional_heuristics": True,
        }

        ancestry_index = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, ancestry_index)
        if not known:
            out = evaluate_family_pressure_forecast(
                family_id=family_id,
                signals={
                    "evidence_sufficient": False,
                    "evidence_warnings": ["FAMILY_NOT_FOUND"],
                },
                thresholds=thresholds,
            )
            out["found"] = False
            out["reason"] = "FAMILY_NOT_FOUND"
            out["forecast_available"] = False
            out["forecast_mode"] = "DIAGNOSTIC_ONLY"
            out["lineage_mutation_performed"] = False
            out["event_creation_performed"] = False
            out.update(threshold_summary)
            return out

        rec = self._families.get(family_id)
        if rec is None:
            out = evaluate_family_pressure_forecast(
                family_id=family_id,
                signals={
                    "evidence_sufficient": False,
                    "evidence_warnings": ["FAMILY_RECORD_NOT_AVAILABLE"],
                },
                thresholds=thresholds,
            )
            out["found"] = True
            out["reason"] = "FAMILY_RECORD_NOT_AVAILABLE"
            out["forecast_available"] = False
            out["forecast_mode"] = "DIAGNOSTIC_ONLY"
            out["lineage_mutation_performed"] = False
            out["event_creation_performed"] = False
            out.update(threshold_summary)
            return out

        member_ids, member_basis = self._family_member_ids_for_fit(rec)
        member_count = len(member_ids)

        topology = self.get_family_topology_audit(family_id)
        topology_metrics = dict(topology.get("topology_metrics", {}))
        geometry_fit = self.get_family_geometry_fit(family_id)
        bridge_count = 0
        edge_count = 0
        for symbol_id in member_ids:
            status = self._earned_boundary_statuses.get(symbol_id)
            if status == "FAMILY_BRIDGE":
                bridge_count += 1
            elif status == "FAMILY_EDGE":
                edge_count += 1

        member_count_float = float(member_count) if member_count > 0 else 1.0
        bridge_fraction = bridge_count / member_count_float
        edge_fraction = edge_count / member_count_float

        evidence_warnings: list[str] = []
        evidence_sufficient = True
        if rec.lifecycle_status != "FAMILY_ACTIVE":
            evidence_sufficient = False
            evidence_warnings.append("FAMILY_PRESSURE_REQUIRES_ACTIVE_FAMILY")
        if member_count < self.PRESSURE_MIN_MEMBERS:
            evidence_sufficient = False
            evidence_warnings.append("INSUFFICIENT_MEMBER_GEOMETRY_FOR_PRESSURE_FORECAST")
        if not bool(topology.get("topology_available", False)):
            evidence_sufficient = False
            evidence_warnings.append("FAMILY_TOPOLOGY_INPUT_INCOMPLETE")
        if not bool(geometry_fit.get("fit_available", False)):
            evidence_sufficient = False
            evidence_warnings.append("FAMILY_GEOMETRY_INPUT_INCOMPLETE")

        transition_event_ids: set[str] = set()
        for evt_id in rec.fission_event_ids:
            if isinstance(evt_id, str) and evt_id:
                transition_event_ids.add(evt_id)
        for evt_id in rec.reunion_event_ids:
            if isinstance(evt_id, str) and evt_id:
                transition_event_ids.add(evt_id)
        if isinstance(rec.lineage_fission_event_id, str) and rec.lineage_fission_event_id:
            transition_event_ids.add(rec.lineage_fission_event_id)
        if isinstance(rec.lineage_reunion_event_id, str) and rec.lineage_reunion_event_id:
            transition_event_ids.add(rec.lineage_reunion_event_id)
        transition_event_count_total = len(transition_event_ids)
        recent_transition_count = min(
            transition_event_count_total,
            int(self.PRESSURE_RECENT_TRANSITION_WINDOW),
        )

        signals = {
            "evidence_sufficient": evidence_sufficient,
            "evidence_warnings": sorted(set(evidence_warnings)),
            "lifecycle_status": rec.lifecycle_status,
            "member_basis": member_basis,
            "member_count": member_count,
            "shape_class": str(topology.get("shape_class", "SHAPE_UNKNOWN")),
            "compression_risk": bool(topology.get("compression_risk", False)),
            "topology_warning_count": len(topology.get("topology_warnings", [])),
            "anisotropy_ratio": float(topology_metrics.get("anisotropy_ratio", 0.0)),
            "pairwise_distance_ratio": float(topology_metrics.get("pairwise_distance_ratio", 0.0)),
            "subgroup_count": int(rec.subgroup_count),
            "subgroup_evidence_counter": int(rec.subgroup_evidence_counter),
            "fracture_status": rec.fracture_status,
            "fracture_counter": int(rec.fracture_counter),
            "fission_candidate_counter": int(rec.fission_candidate_counter),
            "bridge_fraction": float(bridge_fraction),
            "edge_fraction": float(edge_fraction),
            "bridge_symbol_count": int(bridge_count),
            "edge_symbol_count": int(edge_count),
            "geometry_fit_status": str(geometry_fit.get("fit_status", "GEOMETRY_FIT_UNKNOWN")),
            "recent_transition_count": int(recent_transition_count),
            "transition_event_count_total": int(transition_event_count_total),
        }

        out = evaluate_family_pressure_forecast(
            family_id=family_id,
            signals=signals,
            thresholds=thresholds,
        )
        out["found"] = True
        out["reason"] = None if evidence_sufficient else "INSUFFICIENT_STRUCTURAL_EVIDENCE"
        out["forecast_available"] = evidence_sufficient
        out["forecast_mode"] = "DIAGNOSTIC_ONLY"
        out["lineage_mutation_performed"] = False
        out["event_creation_performed"] = False
        out.update(threshold_summary)
        return out

    def get_family_geometry_fit(self, family_id: str) -> dict:
        """
        Returns structural residual metrics for how well family geometry matches member geometry.
        Audit-oriented only; does not mutate lineage or membership.
        """
        ancestry_index = self._build_ancestry_index()
        known = self._family_known_in_ledger_or_records(family_id, ancestry_index)
        if not known:
            return {
                "family_id": family_id,
                "found": False,
                "reason": "FAMILY_NOT_FOUND",
                "fit_available": False,
                "fit_status": "GEOMETRY_FIT_UNKNOWN",
                "fit_warnings": [],
            }

        rec = self._families.get(family_id)
        if rec is None:
            return {
                "family_id": family_id,
                "found": True,
                "reason": "FAMILY_RECORD_NOT_AVAILABLE",
                "fit_available": False,
                "fit_status": "GEOMETRY_FIT_UNKNOWN",
                "fit_warnings": [],
            }

        member_ids, member_basis = self._family_member_ids_for_fit(rec)
        if not member_ids:
            return {
                "family_id": family_id,
                "found": True,
                "reason": "NO_MEMBER_GEOMETRY",
                "fit_available": False,
                "fit_status": "GEOMETRY_FIT_UNKNOWN",
                "fit_warnings": [],
                "member_basis": member_basis,
                "member_symbol_ids_used": [],
            }

        missing_signature_ids = [m_id for m_id in member_ids if m_id not in self._symbol_signatures]
        missing_spread_ids = [m_id for m_id in member_ids if m_id not in self._symbol_spreads]
        if missing_signature_ids or missing_spread_ids:
            return {
                "family_id": family_id,
                "found": True,
                "reason": "MEMBER_GEOMETRY_MISSING",
                "fit_available": False,
                "fit_status": "GEOMETRY_FIT_UNKNOWN",
                "fit_warnings": ["FAMILY_GEOMETRY_INPUT_INCOMPLETE"],
                "member_basis": member_basis,
                "member_symbol_ids_used": member_ids,
                "missing_signature_symbol_ids": sorted(missing_signature_ids),
                "missing_spread_symbol_ids": sorted(missing_spread_ids),
            }

        member_centroid = self._compute_group_centroid(member_ids)
        member_spread_avg = self._compute_group_spread_avg(member_ids)
        family_center = dict(rec.current_signature)
        family_spread = dict(rec.current_spread)

        center_residual = self._calculate_distance(family_center, member_centroid)
        spread_residual = self._calculate_distance(family_spread, member_spread_avg)
        mean_dist_to_family_center = self._mean_distance_to_signature(member_ids, family_center)
        mean_dist_to_member_centroid = self._mean_distance_to_signature(member_ids, member_centroid)
        avg_member_spread = sum(member_spread_avg.values()) / len(member_spread_avg) if member_spread_avg else 0.0

        # Broad-but-honest handling:
        # center residual is normalized by member dispersion/spread baseline, not raw breadth alone.
        center_norm_baseline = max(mean_dist_to_member_centroid, avg_member_spread, 1e-6)
        spread_norm_baseline = max(avg_member_spread, 1e-6)
        center_residual_ratio = center_residual / center_norm_baseline
        spread_residual_ratio = spread_residual / spread_norm_baseline

        center_component = max(
            center_residual / max(self.GEOMETRY_FIT_CENTER_RESIDUAL_MAX, 1e-6),
            center_residual_ratio / max(self.GEOMETRY_FIT_CENTER_RESIDUAL_RATIO_MAX, 1e-6),
        )
        spread_component = max(
            spread_residual / max(self.GEOMETRY_FIT_SPREAD_RESIDUAL_MAX, 1e-6),
            spread_residual_ratio / max(self.GEOMETRY_FIT_SPREAD_RESIDUAL_RATIO_MAX, 1e-6),
        )
        fit_score = max(center_component, spread_component)

        fit_warnings: list[str] = []
        if (
            center_residual > self.GEOMETRY_FIT_CENTER_RESIDUAL_MAX
            or center_residual_ratio > self.GEOMETRY_FIT_CENTER_RESIDUAL_RATIO_MAX
        ):
            fit_warnings.append("FIT_RESIDUAL_HIGH_CENTER")
        if (
            spread_residual > self.GEOMETRY_FIT_SPREAD_RESIDUAL_MAX
            or spread_residual_ratio > self.GEOMETRY_FIT_SPREAD_RESIDUAL_RATIO_MAX
        ):
            fit_warnings.append("FIT_RESIDUAL_HIGH_SPREAD")

        if fit_score <= 1.0:
            fit_status = "GEOMETRY_FIT_GOOD"
        elif fit_score <= self.GEOMETRY_FIT_SCORE_DECAY_MAX:
            fit_status = "FAMILY_GEOMETRY_FIT_DECAY"
            fit_warnings.append("FAMILY_GEOMETRY_FIT_DECAY")
        else:
            fit_status = "FIT_RESIDUAL_HIGH"
            fit_warnings.append("FIT_RESIDUAL_HIGH")

        return {
            "family_id": family_id,
            "found": True,
            "fit_available": True,
            "fit_status": fit_status,
            "fit_score": fit_score,
            "fit_warnings": sorted(set(fit_warnings)),
            "member_basis": member_basis,
            "member_symbol_ids_used": member_ids,
            "member_count_used": len(member_ids),
            "residuals": {
                "center_residual": center_residual,
                "spread_residual": spread_residual,
                "center_residual_ratio": center_residual_ratio,
                "spread_residual_ratio": spread_residual_ratio,
                "mean_member_distance_to_family_center": mean_dist_to_family_center,
                "mean_member_distance_to_member_centroid": mean_dist_to_member_centroid,
                "avg_member_spread": avg_member_spread,
            },
            "family_geometry_snapshot": {
                "current_signature": family_center,
                "current_spread": family_spread,
            },
            "member_geometry_aggregate": {
                "member_centroid": member_centroid,
                "member_spread_avg": member_spread_avg,
            },
            "fit_thresholds": {
                "center_residual_max": float(self.GEOMETRY_FIT_CENTER_RESIDUAL_MAX),
                "center_residual_ratio_max": float(self.GEOMETRY_FIT_CENTER_RESIDUAL_RATIO_MAX),
                "spread_residual_max": float(self.GEOMETRY_FIT_SPREAD_RESIDUAL_MAX),
                "spread_residual_ratio_max": float(self.GEOMETRY_FIT_SPREAD_RESIDUAL_RATIO_MAX),
                "fit_score_decay_max": float(self.GEOMETRY_FIT_SCORE_DECAY_MAX),
            },
            "fit_metric_description": {
                "center_residual": "distance(family.current_signature, aggregate(member_signatures))",
                "spread_residual": "distance(family.current_spread, aggregate(member_spreads))",
                "fit_score": "max(normalized_center_component, normalized_spread_component)",
            },
        }

    def get_transition_geometry_fit(self, event_id: str) -> dict:
        """
        Returns event-centered geometric lineage fit summary for one transition event.
        Audit-oriented only; does not mutate lineage.
        """
        evt, duplicate_count = self._get_ledger_event_by_id(event_id)
        if evt is None:
            return {
                "event_id": event_id,
                "found": False,
                "reason": "EVENT_NOT_FOUND",
                "fit_available": False,
                "fit_status": "GEOMETRY_FIT_UNKNOWN",
                "fit_warnings": [],
            }

        source_ids = sorted([x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x])
        successor_ids = sorted([x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x])
        participant_ids = sorted(set(source_ids + successor_ids))

        participant_family_fits = [self.get_family_geometry_fit(fam_id) for fam_id in participant_ids]
        weak_families = sorted(
            [
                x["family_id"]
                for x in participant_family_fits
                if x.get("fit_available") and x.get("fit_status") in {"FIT_RESIDUAL_HIGH", "FAMILY_GEOMETRY_FIT_DECAY"}
            ]
        )

        continuity_center_residual = None
        continuity_ok = None
        continuity_member_ids: list[str] = []
        member_summary = self._build_event_member_summary(evt)
        continuity_member_ids = [x for x in member_summary.get("member_ids", []) if isinstance(x, str) and x]
        if continuity_member_ids:
            missing = [m_id for m_id in continuity_member_ids if m_id not in self._symbol_signatures]
            if not missing:
                member_centroid = self._compute_group_centroid(continuity_member_ids)
                if evt.get("event_type") == "FAMILY_FISSION_V1" and source_ids:
                    src_rec = self._families.get(source_ids[0])
                    if src_rec is not None:
                        continuity_center_residual = self._calculate_distance(src_rec.current_signature, member_centroid)
                elif evt.get("event_type") == "FAMILY_REUNION_V1" and successor_ids:
                    succ_rec = self._families.get(successor_ids[0])
                    if succ_rec is not None:
                        continuity_center_residual = self._calculate_distance(succ_rec.current_signature, member_centroid)
                if continuity_center_residual is not None:
                    continuity_ok = continuity_center_residual <= self.TRANSITION_CONTINUITY_CENTER_RESIDUAL_MAX

        fit_warnings: list[str] = []
        fit_status = "GEOMETRY_FIT_GOOD"
        event_type = str(evt.get("event_type", ""))

        weak_successors = [
            x["family_id"]
            for x in participant_family_fits
            if x.get("family_id") in successor_ids
            and x.get("fit_available")
            and x.get("fit_status") in {"FIT_RESIDUAL_HIGH", "FAMILY_GEOMETRY_FIT_DECAY"}
        ]

        if event_type == "FAMILY_FISSION_V1" and weak_successors:
            fit_warnings.append("SUCCESSOR_GEOMETRY_FIT_WEAK")
        if event_type == "FAMILY_REUNION_V1" and weak_successors:
            fit_warnings.append("REUNION_GEOMETRY_FIT_WEAK")
        if continuity_ok is False:
            fit_warnings.append("LINEAGE_CONTINUITY_CENTER_RESIDUAL_HIGH")
        if weak_families:
            fit_warnings.append("FIT_RESIDUAL_HIGH")

        if fit_warnings:
            fit_status = "FIT_RESIDUAL_HIGH"
        elif weak_families:
            fit_status = "FAMILY_GEOMETRY_FIT_DECAY"

        return {
            "event_id": event_id,
            "found": True,
            "fit_available": True,
            "fit_status": fit_status,
            "fit_warnings": sorted(set(fit_warnings)),
            "event_identity": {
                "event_type": evt.get("event_type"),
                "event_order": evt.get("event_order"),
                "ledger_write_order": evt.get("ledger_write_order"),
                "duplicate_event_id_count_in_ledger": int(duplicate_count),
            },
            "participants": {
                "source_family_ids": source_ids,
                "successor_family_ids": successor_ids,
                "participant_family_ids": participant_ids,
            },
            "participant_family_fits": participant_family_fits,
            "lineage_continuity": {
                "continuity_member_ids": continuity_member_ids,
                "continuity_member_count": len(continuity_member_ids),
                "continuity_center_residual": continuity_center_residual,
                "continuity_center_residual_max": float(self.TRANSITION_CONTINUITY_CENTER_RESIDUAL_MAX),
                "continuity_ok": continuity_ok,
            },
        }

    def get_transition_topology_audit(self, event_id: str) -> dict:
        """
        Returns event-centered topology/shape summary for participant families.
        Audit-oriented only; does not mutate lineage.
        """
        evt, duplicate_count = self._get_ledger_event_by_id(event_id)
        if evt is None:
            return {
                "event_id": event_id,
                "found": False,
                "reason": "EVENT_NOT_FOUND",
                "topology_available": False,
                "topology_warnings": [],
            }

        source_ids = sorted([x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x])
        successor_ids = sorted([x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x])
        participant_ids = sorted(set(source_ids + successor_ids))
        participant_topology = [self.get_family_topology_audit(fam_id) for fam_id in participant_ids]

        compression_risk_family_ids = sorted(
            [
                x["family_id"]
                for x in participant_topology
                if x.get("topology_available") and bool(x.get("compression_risk"))
            ]
        )

        topology_warnings: list[str] = []
        if compression_risk_family_ids:
            topology_warnings.append("TOPOLOGY_COMPRESSION_RISK")

        return {
            "event_id": event_id,
            "found": True,
            "topology_available": True,
            "topology_warnings": sorted(set(topology_warnings)),
            "event_identity": {
                "event_type": evt.get("event_type"),
                "event_order": evt.get("event_order"),
                "ledger_write_order": evt.get("ledger_write_order"),
                "duplicate_event_id_count_in_ledger": int(duplicate_count),
            },
            "participants": {
                "source_family_ids": source_ids,
                "successor_family_ids": successor_ids,
                "participant_family_ids": participant_ids,
            },
            "participant_topology": participant_topology,
            "compression_risk_family_ids": compression_risk_family_ids,
        }

    def get_transition_pressure_snapshot(self, event_id: str) -> dict:
        """
        Returns an event-centered pressure snapshot from recoverable event-linked evidence only.

        Honesty posture:
        - no mutation
        - no history rewrite
        - no reconstruction from current family state when event-time evidence is absent
        """
        evt, duplicate_count = self._get_ledger_event_by_id(event_id)
        if evt is None:
            return {
                "event_id": event_id,
                "found": False,
                "snapshot_available": False,
                "snapshot_mode": "EVENT_LINKED_RECOVERABLE_ONLY",
                "reason": "EVENT_NOT_FOUND",
                "event_type": None,
                "event_metadata": None,
                "participant_family_ids": [],
                "participants": None,
                "pre_event_pressure": None,
                "post_event_pressure": None,
                "evidence_flags": {
                    "event_found": False,
                    "participant_ids_available": False,
                    "event_pressure_snapshot_field_present": False,
                    "pre_event_pressure_recoverable": False,
                    "post_event_pressure_recoverable": False,
                    "recovered_from_event_record_only": True,
                    "inferred_from_current_family_state": False,
                    "duplicate_event_id_count_in_ledger": 0,
                },
                "warnings": ["EVENT_NOT_FOUND"],
                "explanation_lines": ["Event ID is not present in durable ledger; snapshot unavailable."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        source_ids = sorted([x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x])
        successor_ids = sorted([x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x])
        participant_ids = sorted(set(source_ids + successor_ids))

        pressure_snapshot = evt.get("pressure_snapshot")
        pre_candidate = None
        post_candidate = None
        capture_metadata = None
        pressure_snapshot_field_present = False
        if isinstance(pressure_snapshot, dict):
            pressure_snapshot_field_present = True
            pre_candidate = pressure_snapshot.get("pre_event_pressure")
            post_candidate = pressure_snapshot.get("post_event_pressure")
            capture_metadata = {
                "capture_attempted": bool(pressure_snapshot.get("capture_attempted", False)),
                "capture_succeeded": bool(pressure_snapshot.get("capture_succeeded", False)),
                "capture_mode": pressure_snapshot.get("capture_mode"),
                "capture_reason": pressure_snapshot.get("capture_reason"),
                "pre_capture_status_by_family": dict(pressure_snapshot.get("pre_capture_status_by_family", {}))
                if isinstance(pressure_snapshot.get("pre_capture_status_by_family"), dict)
                else {},
                "post_capture_status_by_family": dict(pressure_snapshot.get("post_capture_status_by_family", {}))
                if isinstance(pressure_snapshot.get("post_capture_status_by_family"), dict)
                else {},
            }
        else:
            if "pre_event_pressure" in evt or "post_event_pressure" in evt:
                pressure_snapshot_field_present = True
            pre_candidate = evt.get("pre_event_pressure")
            post_candidate = evt.get("post_event_pressure")

        pre_recoverable = isinstance(pre_candidate, dict) and bool(pre_candidate)
        post_recoverable = isinstance(post_candidate, dict) and bool(post_candidate)
        pre_event_pressure = json.loads(json.dumps(pre_candidate, sort_keys=True)) if pre_recoverable else None
        post_event_pressure = json.loads(json.dumps(post_candidate, sort_keys=True)) if post_recoverable else None

        warnings: list[str] = []
        explanation_lines: list[str] = []
        if duplicate_count > 1:
            warnings.append("DUPLICATE_EVENT_ID_IN_LEDGER")
            explanation_lines.append("Duplicate event_id entries found in ledger; using first occurrence.")
        if not participant_ids:
            warnings.append("EVENT_PARTICIPANT_IDS_MISSING")
            explanation_lines.append("Event has no participant family IDs.")
        if not pressure_snapshot_field_present:
            warnings.append("EVENT_PRESSURE_SNAPSHOT_NOT_STORED")
            explanation_lines.append("Event does not store pressure snapshot fields.")
        if not pre_recoverable:
            warnings.append("PRE_EVENT_PRESSURE_UNRECOVERABLE")
        if not post_recoverable:
            warnings.append("POST_EVENT_PRESSURE_UNRECOVERABLE")
        if pressure_snapshot_field_present and pre_candidate is not None and not pre_recoverable:
            warnings.append("PRE_EVENT_PRESSURE_FORMAT_UNSUPPORTED")
        if pressure_snapshot_field_present and post_candidate is not None and not post_recoverable:
            warnings.append("POST_EVENT_PRESSURE_FORMAT_UNSUPPORTED")

        snapshot_available = bool(pre_recoverable or post_recoverable)
        reason = "PRESSURE_SNAPSHOT_UNRECOVERABLE"
        if pre_recoverable and post_recoverable:
            reason = "PRESSURE_SNAPSHOT_RECOVERED"
            explanation_lines.append("Both pre-event and post-event pressure snapshots were recovered from event-linked fields.")
        elif snapshot_available:
            reason = "PRESSURE_SNAPSHOT_PARTIAL"
            explanation_lines.append("Only partial event-linked pressure snapshot is recoverable.")
        else:
            explanation_lines.append("No recoverable event-time pressure snapshot; current family state was not used for reconstruction.")

        return {
            "event_id": event_id,
            "found": True,
            "snapshot_available": snapshot_available,
            "snapshot_mode": "EVENT_LINKED_RECOVERABLE_ONLY",
            "reason": reason,
            "event_type": evt.get("event_type"),
            "event_metadata": {
                "event_type": evt.get("event_type"),
                "event_order": evt.get("event_order"),
                "ledger_write_order": evt.get("ledger_write_order"),
                "ledger_timestamp_utc": evt.get("ledger_timestamp_utc"),
                "duplicate_event_id_count_in_ledger": int(duplicate_count),
            },
            "capture_metadata": capture_metadata,
            "participant_family_ids": participant_ids,
            "participants": {
                "source_family_ids": source_ids,
                "successor_family_ids": successor_ids,
                "participant_family_ids": participant_ids,
            },
            "pre_event_pressure": pre_event_pressure,
            "post_event_pressure": post_event_pressure,
            "evidence_flags": {
                "event_found": True,
                "participant_ids_available": bool(participant_ids),
                "event_pressure_snapshot_field_present": pressure_snapshot_field_present,
                "pre_event_pressure_recoverable": pre_recoverable,
                "post_event_pressure_recoverable": post_recoverable,
                "recovered_from_event_record_only": True,
                "inferred_from_current_family_state": False,
                "duplicate_event_id_count_in_ledger": int(duplicate_count),
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_transition_cross_band_self_check(self, event_id: str) -> dict:
        """
        Read-only cross-band honesty check for one transition event.

        v1.0a rule posture:
        - pressure is the primary trusted directional signal
        - adjacent topology is lower-confidence supporting evidence only
        - missing/weak evidence stays PARTIAL or UNAVAILABLE (no forced certainty)
        """
        evt, duplicate_count = self._get_ledger_event_by_id(event_id)
        if evt is None:
            return {
                "event_id": event_id,
                "found": False,
                "audit_available": False,
                "audit_mode": "CROSS_BAND_SELF_CHECK",
                "self_check_state": "CROSS_BAND_UNAVAILABLE",
                "reason": "EVENT_NOT_FOUND",
                "event_type": None,
                "participant_family_ids": [],
                "evidence_surface": {
                    "pressure_available": False,
                    "topology_available": False,
                    "event_snapshot_available": False,
                    "pre_event_directional_signal": "PRESSURE_SIGNAL_UNAVAILABLE",
                    "post_event_outcome_signal": "OUTCOME_UNKNOWN",
                    "recoverability_notes": ["EVENT_NOT_FOUND"],
                },
                "directional_alignment": {
                    "pressure_alignment": "PRESSURE_ALIGNMENT_UNAVAILABLE",
                    "topology_alignment": "TOPOLOGY_ALIGNMENT_UNAVAILABLE",
                    "overall_alignment": "OVERALL_ALIGNMENT_UNAVAILABLE",
                    "confidence_posture": "CONFIDENCE_NONE",
                },
                "contradiction_flags": ["EVIDENCE_INSUFFICIENT"],
                "warnings": ["EVENT_NOT_FOUND"],
                "explanation_lines": ["Event ID is not present in durable ledger; cross-band self-check unavailable."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        source_ids = sorted([x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x])
        successor_ids = sorted([x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x])
        participant_ids = sorted(set(source_ids + successor_ids))

        event_type = str(evt.get("event_type", ""))
        if event_type.startswith("FAMILY_FISSION"):
            outcome_signal = "OUTCOME_FISSION"
        elif event_type.startswith("FAMILY_REUNION"):
            outcome_signal = "OUTCOME_REUNION"
        else:
            outcome_signal = "OUTCOME_UNKNOWN"

        snapshot = self.get_transition_pressure_snapshot(event_id)
        topology = self.get_transition_topology_audit(event_id)

        warnings: list[str] = []
        explanation_lines: list[str] = []
        if duplicate_count > 1:
            warnings.append("DUPLICATE_EVENT_ID_IN_LEDGER")
        if not participant_ids:
            warnings.append("EVENT_PARTICIPANT_IDS_MISSING")

        pre_event_recoverable = bool(snapshot.get("evidence_flags", {}).get("pre_event_pressure_recoverable", False))
        event_snapshot_available = bool(snapshot.get("snapshot_available", False))

        pre_event_pressure = snapshot.get("pre_event_pressure")
        pressure_states: list[str] = []
        if isinstance(pre_event_pressure, dict):
            by_id = pre_event_pressure.get("family_pressure_by_id")
            if isinstance(by_id, dict):
                for fam_id in sorted(by_id.keys()):
                    fam_payload = by_id.get(fam_id)
                    if isinstance(fam_payload, dict):
                        state = fam_payload.get("pressure_state")
                        if isinstance(state, str) and state:
                            pressure_states.append(state)
            direct_state = pre_event_pressure.get("pressure_state")
            if isinstance(direct_state, str) and direct_state:
                pressure_states.append(direct_state)
        pressure_states = sorted(set(pressure_states))

        split_oriented_pressure_states = {"PRESSURE_DUAL_CENTER_RISK", "PRESSURE_FISSION_PRONE"}
        pressure_classes: set[str] = set()
        saw_unrecognized_pressure_state = False
        for state in pressure_states:
            if state in split_oriented_pressure_states:
                pressure_classes.add("SPLIT")
            elif state == "PRESSURE_STABLE":
                pressure_classes.add("STABLE")
            elif state == "PRESSURE_STRETCHED":
                pressure_classes.add("STRETCHED")
            elif state == "PRESSURE_UNCLEAR":
                pressure_classes.add("UNCLEAR")
            else:
                saw_unrecognized_pressure_state = True

        if not pre_event_recoverable:
            pre_event_directional_signal = "PRESSURE_SIGNAL_UNAVAILABLE"
        elif not pressure_states:
            pre_event_directional_signal = "PRESSURE_SIGNAL_UNCLASSIFIED"
        elif len(pressure_classes) == 1 and not saw_unrecognized_pressure_state:
            cls = next(iter(pressure_classes))
            if cls == "SPLIT":
                pre_event_directional_signal = "PRESSURE_SIGNAL_SPLIT_ORIENTED"
            elif cls == "STABLE":
                pre_event_directional_signal = "PRESSURE_SIGNAL_STABLE"
            elif cls == "STRETCHED":
                pre_event_directional_signal = "PRESSURE_SIGNAL_STRETCHED"
            elif cls == "UNCLEAR":
                pre_event_directional_signal = "PRESSURE_SIGNAL_UNCLEAR"
            else:
                pre_event_directional_signal = "PRESSURE_SIGNAL_UNCLASSIFIED"
        elif pressure_classes or saw_unrecognized_pressure_state:
            pre_event_directional_signal = "PRESSURE_SIGNAL_MIXED"
        else:
            pre_event_directional_signal = "PRESSURE_SIGNAL_UNCLASSIFIED"

        topology_audit_available = bool(topology.get("topology_available", False))
        participant_topology = topology.get("participant_topology", [])
        if not isinstance(participant_topology, list):
            participant_topology = []

        has_split_topology = False
        has_non_split_topology = False
        has_topology_member_evidence = False
        for topo in participant_topology:
            if not isinstance(topo, dict):
                continue
            if not bool(topo.get("topology_available", False)):
                continue
            has_topology_member_evidence = True
            shape_class = str(topo.get("shape_class", "SHAPE_UNKNOWN"))
            compression_risk = bool(topo.get("compression_risk", False))
            if shape_class == "SHAPE_DUAL_LOBE" or compression_risk:
                has_split_topology = True
            if shape_class == "SHAPE_COMPACT" and not compression_risk:
                has_non_split_topology = True

        topology_signal_recoverable = topology_audit_available and has_topology_member_evidence
        if not topology_signal_recoverable:
            topology_directional_signal = "TOPOLOGY_SIGNAL_UNAVAILABLE"
        elif has_split_topology:
            topology_directional_signal = "TOPOLOGY_SIGNAL_SPLIT_ORIENTED_ADJACENT"
        elif has_non_split_topology:
            topology_directional_signal = "TOPOLOGY_SIGNAL_NON_SPLIT_ADJACENT"
        else:
            topology_directional_signal = "TOPOLOGY_SIGNAL_UNCLEAR_ADJACENT"

        pressure_alignment = "PRESSURE_ALIGNMENT_UNAVAILABLE"
        topology_alignment = "TOPOLOGY_ALIGNMENT_UNAVAILABLE"
        contradiction_flags: list[str] = []
        recoverability_notes: list[str] = []

        if pre_event_recoverable:
            recoverability_notes.append("PRE_EVENT_PRESSURE_RECOVERED_FROM_EVENT_LINKED_SNAPSHOT")
        else:
            recoverability_notes.append("PRE_EVENT_PRESSURE_UNRECOVERABLE_FROM_EVENT_LINKED_SNAPSHOT")

        if topology_signal_recoverable:
            recoverability_notes.append("TOPOLOGY_FROM_ADJACENT_TRANSITION_AUDIT_SURFACE")
        elif topology_audit_available:
            recoverability_notes.append("TOPOLOGY_DIRECTIONAL_SIGNAL_UNRECOVERABLE")
        else:
            recoverability_notes.append("TOPOLOGY_SIGNAL_UNAVAILABLE")

        if outcome_signal == "OUTCOME_UNKNOWN":
            warnings.append("UNSUPPORTED_TRANSITION_EVENT_TYPE")
            recoverability_notes.append("EVENT_TYPE_UNSUPPORTED_FOR_DIRECTIONAL_CHECK")
            explanation_lines.append("Event type is unsupported for directional self-check.")
        else:
            if pre_event_recoverable:
                if outcome_signal == "OUTCOME_FISSION":
                    if pre_event_directional_signal == "PRESSURE_SIGNAL_SPLIT_ORIENTED":
                        pressure_alignment = "PRESSURE_ALIGNMENT_OBSERVED"
                    elif pre_event_directional_signal == "PRESSURE_SIGNAL_STABLE":
                        pressure_alignment = "PRESSURE_ALIGNMENT_CONTRADICTION"
                        contradiction_flags.append("PRESSURE_EVENT_DIRECTION_CONTRADICTION")
                    else:
                        pressure_alignment = "PRESSURE_ALIGNMENT_PARTIAL"
                else:
                    if pre_event_directional_signal == "PRESSURE_SIGNAL_SPLIT_ORIENTED":
                        pressure_alignment = "PRESSURE_ALIGNMENT_CONTRADICTION"
                        contradiction_flags.append("PRESSURE_EVENT_DIRECTION_CONTRADICTION")
                    elif pre_event_directional_signal == "PRESSURE_SIGNAL_STABLE":
                        pressure_alignment = "PRESSURE_ALIGNMENT_OBSERVED"
                    else:
                        pressure_alignment = "PRESSURE_ALIGNMENT_PARTIAL"

            if topology_signal_recoverable:
                if outcome_signal == "OUTCOME_FISSION":
                    if topology_directional_signal == "TOPOLOGY_SIGNAL_SPLIT_ORIENTED_ADJACENT":
                        topology_alignment = "TOPOLOGY_ALIGNMENT_OBSERVED_ADJACENT"
                    elif topology_directional_signal == "TOPOLOGY_SIGNAL_NON_SPLIT_ADJACENT":
                        topology_alignment = "TOPOLOGY_ALIGNMENT_PARTIAL_ADJACENT"
                    else:
                        topology_alignment = "TOPOLOGY_ALIGNMENT_PARTIAL_ADJACENT"
                else:
                    if topology_directional_signal == "TOPOLOGY_SIGNAL_SPLIT_ORIENTED_ADJACENT":
                        topology_alignment = "TOPOLOGY_ALIGNMENT_CONTRADICTION_ADJACENT"
                        contradiction_flags.append("TOPOLOGY_EVENT_DIRECTION_CONTRADICTION")
                    elif topology_directional_signal == "TOPOLOGY_SIGNAL_NON_SPLIT_ADJACENT":
                        topology_alignment = "TOPOLOGY_ALIGNMENT_OBSERVED_ADJACENT"
                    else:
                        topology_alignment = "TOPOLOGY_ALIGNMENT_PARTIAL_ADJACENT"

        trusted_pressure_contradiction = pressure_alignment == "PRESSURE_ALIGNMENT_CONTRADICTION"
        trusted_pressure_alignment = pressure_alignment == "PRESSURE_ALIGNMENT_OBSERVED"
        pressure_directional_evidence = pressure_alignment in {
            "PRESSURE_ALIGNMENT_OBSERVED",
            "PRESSURE_ALIGNMENT_CONTRADICTION",
            "PRESSURE_ALIGNMENT_PARTIAL",
        }
        topology_directional_evidence = topology_directional_signal in {
            "TOPOLOGY_SIGNAL_SPLIT_ORIENTED_ADJACENT",
            "TOPOLOGY_SIGNAL_NON_SPLIT_ADJACENT",
        }
        has_any_directional_evidence = pressure_directional_evidence or topology_directional_evidence

        # Explicit v1.0a precedence:
        # 1) unsupported outcome/no directional evidence -> UNAVAILABLE
        # 2) trusted pressure contradiction -> CONTRADICTION_OBSERVED
        # 3) trusted pressure alignment and no trusted contradiction -> ALIGNMENT_OBSERVED
        # 4) mixed/weak/adjacent-only recoverable evidence -> PARTIAL
        # 5) fallback -> UNAVAILABLE
        if outcome_signal == "OUTCOME_UNKNOWN" or not has_any_directional_evidence:
            self_check_state = "CROSS_BAND_UNAVAILABLE"
            reason = "INSUFFICIENT_DIRECTIONAL_EVIDENCE"
            overall_alignment = "OVERALL_ALIGNMENT_UNAVAILABLE"
            confidence_posture = "CONFIDENCE_NONE"
            contradiction_flags.append("EVIDENCE_INSUFFICIENT")
            explanation_lines.append("No recoverable directional evidence surface is available for this event.")
        elif trusted_pressure_contradiction:
            self_check_state = "CROSS_BAND_CONTRADICTION_OBSERVED"
            reason = "DIRECTIONAL_CONTRADICTION_OBSERVED"
            overall_alignment = "OVERALL_ALIGNMENT_CONTRADICTION"
            confidence_posture = "CONFIDENCE_EVENT_LINKED_PRESSURE_PRIMARY"
            explanation_lines.append("Trusted event-linked pressure signal contradicts the recorded transition direction.")
        elif trusted_pressure_alignment:
            self_check_state = "CROSS_BAND_ALIGNMENT_OBSERVED"
            reason = "DIRECTIONAL_ALIGNMENT_OBSERVED"
            overall_alignment = "OVERALL_ALIGNMENT_OBSERVED"
            confidence_posture = "CONFIDENCE_EVENT_LINKED_PRESSURE_PRIMARY"
            if not any(flag in contradiction_flags for flag in {"PRESSURE_EVENT_DIRECTION_CONTRADICTION", "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION"}):
                contradiction_flags.append("NO_CONTRADICTION_OBSERVED")
            if "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION" in contradiction_flags:
                explanation_lines.append(
                    "Trusted pressure alignment is observed; adjacent topology contradiction is retained as a low-confidence note."
                )
            else:
                explanation_lines.append("Trusted event-linked pressure signal aligns with the recorded transition direction.")
        elif has_any_directional_evidence:
            self_check_state = "CROSS_BAND_PARTIAL"
            reason = "PARTIAL_DIRECTIONAL_EVIDENCE"
            overall_alignment = "OVERALL_ALIGNMENT_PARTIAL"
            if pressure_directional_evidence and pre_event_recoverable:
                confidence_posture = "CONFIDENCE_EVENT_LINKED_PRESSURE_PARTIAL"
            elif topology_directional_evidence:
                confidence_posture = "CONFIDENCE_ADJACENT_TOPOLOGY_ONLY_LOW"
            else:
                confidence_posture = "CONFIDENCE_NONE"
            contradiction_flags.append("EVIDENCE_INSUFFICIENT")
            if "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION" in contradiction_flags and not trusted_pressure_contradiction:
                explanation_lines.append(
                    "Adjacent topology indicates contradiction, but trusted pressure contradiction is absent; state remains PARTIAL."
                )
            else:
                explanation_lines.append("Directional evidence is recoverable but weak or mixed; state remains PARTIAL.")
        else:
            self_check_state = "CROSS_BAND_UNAVAILABLE"
            reason = "INSUFFICIENT_DIRECTIONAL_EVIDENCE"
            overall_alignment = "OVERALL_ALIGNMENT_UNAVAILABLE"
            confidence_posture = "CONFIDENCE_NONE"
            contradiction_flags.append("EVIDENCE_INSUFFICIENT")
            explanation_lines.append("Directional evidence is unavailable.")

        evidence_surface = {
            "pressure_available": pre_event_recoverable,
            "topology_available": topology_signal_recoverable,
            "event_snapshot_available": event_snapshot_available,
            "pre_event_directional_signal": pre_event_directional_signal,
            "post_event_outcome_signal": outcome_signal,
            "recoverability_notes": recoverability_notes,
        }
        directional_alignment = {
            "pressure_alignment": pressure_alignment,
            "topology_alignment": topology_alignment,
            "overall_alignment": overall_alignment,
            "confidence_posture": confidence_posture,
        }

        return {
            "event_id": event_id,
            "found": True,
            "audit_available": True,
            "audit_mode": "CROSS_BAND_SELF_CHECK",
            "self_check_state": self_check_state,
            "reason": reason,
            "event_type": evt.get("event_type"),
            "participant_family_ids": participant_ids,
            "evidence_surface": evidence_surface,
            "directional_alignment": directional_alignment,
            "contradiction_flags": sorted(set(contradiction_flags)),
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_cross_band_self_check_summary_window(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Read-only bounded count sampler over transition cross-band self-check outputs.
        Index behavior:
        - start_index: inclusive
        - end_index: exclusive
        - max_events: truncates deterministically after index bounds resolution
        """
        def _is_valid_bound(v: Optional[int]) -> bool:
            return v is None or isinstance(v, int)

        def _norm_event_type(event_type: str) -> str:
            if event_type.startswith("FAMILY_FISSION"):
                return "FAMILY_FISSION"
            if event_type.startswith("FAMILY_REUNION"):
                return "FAMILY_REUNION"
            return event_type

        def _empty_state_counts() -> dict:
            return {
                "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                "CROSS_BAND_PARTIAL": 0,
                "CROSS_BAND_UNAVAILABLE": 0,
            }

        def _empty_contradiction_counts() -> dict:
            return {
                "PRESSURE_EVENT_DIRECTION_CONTRADICTION": 0,
                "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION": 0,
                "EVIDENCE_INSUFFICIENT": 0,
                "NO_CONTRADICTION_OBSERVED": 0,
            }

        invalid_bounds = (
            (not _is_valid_bound(start_index))
            or (not _is_valid_bound(end_index))
            or (not _is_valid_bound(max_events))
            or (isinstance(start_index, int) and start_index < 0)
            or (isinstance(end_index, int) and end_index < 0)
            or (isinstance(max_events, int) and max_events < 0)
            or (
                isinstance(start_index, int)
                and isinstance(end_index, int)
                and end_index < start_index
            )
        )

        ledger_events = self.get_event_ledger()
        transition_records, skipped_non_transition_count = self._select_eligible_transition_events(ledger_events)
        total_transition_events = len(transition_records)

        requested_start = start_index
        requested_end = end_index
        requested_max_events = max_events

        if invalid_bounds:
            warnings: list[str] = ["INVALID_WINDOW_BOUNDS"]
            lines: list[str] = ["Window bounds were invalid; cross-band self-check summary not computed for requested slice."]
            if skipped_non_transition_count > 0:
                warnings.append("NON_TRANSITION_LEDGER_RECORDS_SKIPPED")
                lines.append("Non-transition ledger records were skipped from eligible transition selection.")
            return {
                "summary_available": False,
                "summary_mode": "CROSS_BAND_SELF_CHECK_WINDOW",
                "reason": "INVALID_WINDOW_BOUNDS",
                "window_spec": {
                    "start_index": requested_start,
                    "end_index": requested_end,
                    "max_events": requested_max_events,
                    "applied_start_index": None,
                    "applied_end_index": None,
                    "applied_event_count": 0,
                },
                "total_transition_events": total_transition_events,
                "window_event_count": 0,
                "auditable_event_count": 0,
                "self_check_state_counts": _empty_state_counts(),
                "contradiction_flag_counts": _empty_contradiction_counts(),
                "event_type_counts": {},
                "warnings": sorted(set(warnings)),
                "explanation_lines": lines,
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        resolved_start = 0 if start_index is None else start_index
        resolved_end = len(transition_records) if end_index is None else end_index
        sliced_records = transition_records[resolved_start:resolved_end]
        if max_events is not None:
            sliced_records = sliced_records[:max_events]

        window_event_count = len(sliced_records)
        applied_start = resolved_start
        applied_end = resolved_start + window_event_count

        state_counts = _empty_state_counts()
        contradiction_flag_counts = _empty_contradiction_counts()
        event_type_counts: dict[str, int] = {}
        warnings: list[str] = []
        explanation_lines: list[str] = []

        unique_records: list[dict] = []
        seen_ids: set[str] = set()
        duplicate_event_id_count = 0
        for evt in sliced_records:
            event_id = str(evt.get("event_id", ""))
            if event_id in seen_ids:
                duplicate_event_id_count += 1
                continue
            seen_ids.add(event_id)
            unique_records.append(evt)

        auditable_event_count = 0
        for evt in unique_records:
            event_id = str(evt.get("event_id", ""))
            event_type_norm = _norm_event_type(str(evt.get("event_type", "")))
            event_type_counts[event_type_norm] = event_type_counts.get(event_type_norm, 0) + 1

            check = self.get_transition_cross_band_self_check(event_id)
            auditable_event_count += 1

            check_state = str(check.get("self_check_state", "CROSS_BAND_UNAVAILABLE"))
            if not bool(check.get("audit_available", False)):
                check_state = "CROSS_BAND_UNAVAILABLE"
            if check_state not in state_counts:
                warnings.append("UNRECOGNIZED_SELF_CHECK_STATE")
                check_state = "CROSS_BAND_UNAVAILABLE"
            state_counts[check_state] += 1

            raw_flags = check.get("contradiction_flags", [])
            if isinstance(raw_flags, list):
                for flag in raw_flags:
                    if not isinstance(flag, str) or not flag:
                        continue
                    if flag not in contradiction_flag_counts:
                        contradiction_flag_counts[flag] = 0
                    contradiction_flag_counts[flag] += 1

        reason = "OK"
        if total_transition_events == 0:
            reason = "NO_TRANSITION_EVENTS"
            explanation_lines.append("No eligible durable transition events available for cross-band self-check window summary.")
        elif window_event_count == 0:
            reason = "EMPTY_WINDOW_SELECTION"
            warnings.append("EMPTY_WINDOW_SELECTION")
            explanation_lines.append("Window selection contains zero eligible transition events.")
        else:
            explanation_lines.append("Cross-band self-check window summary composed from per-event self-check outputs only.")

        if duplicate_event_id_count > 0:
            warnings.append("DUPLICATE_EVENT_ID_IN_LEDGER")
            explanation_lines.append(
                "Duplicate event_id records were detected in selected window; counts use first occurrence per event_id."
            )
        if skipped_non_transition_count > 0:
            warnings.append("NON_TRANSITION_LEDGER_RECORDS_SKIPPED")
            explanation_lines.append("Non-transition ledger records were skipped from eligible transition selection.")

        return {
            "summary_available": True,
            "summary_mode": "CROSS_BAND_SELF_CHECK_WINDOW",
            "reason": reason,
            "window_spec": {
                "start_index": requested_start,
                "end_index": requested_end,
                "max_events": requested_max_events,
                "applied_start_index": applied_start,
                "applied_end_index": applied_end,
                "applied_event_count": window_event_count,
            },
            "total_transition_events": total_transition_events,
            "window_event_count": window_event_count,
            "auditable_event_count": auditable_event_count,
            "self_check_state_counts": state_counts,
            "contradiction_flag_counts": {k: contradiction_flag_counts[k] for k in sorted(contradiction_flag_counts.keys())},
            "event_type_counts": dict(sorted(event_type_counts.items())),
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_cross_band_self_check_summary_event_order_window(
        self,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Read-only event_order-window count sampler over transition cross-band self-check outputs.
        Event-order behavior:
        - start_event_order: inclusive
        - end_event_order: inclusive
        - max_events: truncates deterministically after event_order filtering
        - deterministic tie behavior: (event_order asc, transition-ledger-sequence asc)
        """
        def _is_valid_order_bound(v: Optional[float]) -> bool:
            if v is None:
                return True
            if isinstance(v, bool):
                return False
            if isinstance(v, (int, float)):
                return math.isfinite(float(v))
            return False

        def _is_valid_max_events(v: Optional[int]) -> bool:
            if v is None:
                return True
            if isinstance(v, bool):
                return False
            return isinstance(v, int)

        def _norm_event_type(event_type: str) -> str:
            if event_type.startswith("FAMILY_FISSION"):
                return "FAMILY_FISSION"
            if event_type.startswith("FAMILY_REUNION"):
                return "FAMILY_REUNION"
            return event_type

        def _empty_state_counts() -> dict:
            return {
                "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                "CROSS_BAND_PARTIAL": 0,
                "CROSS_BAND_UNAVAILABLE": 0,
            }

        def _empty_contradiction_counts() -> dict:
            return {
                "PRESSURE_EVENT_DIRECTION_CONTRADICTION": 0,
                "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION": 0,
                "EVIDENCE_INSUFFICIENT": 0,
                "NO_CONTRADICTION_OBSERVED": 0,
            }

        invalid_bounds = (
            (not _is_valid_order_bound(start_event_order))
            or (not _is_valid_order_bound(end_event_order))
            or (not _is_valid_max_events(max_events))
            or (isinstance(max_events, int) and max_events < 0)
            or (
                isinstance(start_event_order, (int, float))
                and isinstance(end_event_order, (int, float))
                and float(end_event_order) < float(start_event_order)
            )
        )

        ledger_events = self.get_event_ledger()
        transition_records, skipped_non_transition_count = self._select_eligible_transition_events(ledger_events)
        total_transition_events = len(transition_records)

        requested_start = start_event_order
        requested_end = end_event_order
        requested_max_events = max_events

        event_order_eligible: list[tuple[float, int, dict]] = []
        missing_or_unusable_event_order_count = 0
        for seq, evt in enumerate(transition_records):
            raw_order = evt.get("event_order")
            if isinstance(raw_order, bool) or not isinstance(raw_order, (int, float)):
                missing_or_unusable_event_order_count += 1
                continue
            order_value = float(raw_order)
            if not math.isfinite(order_value):
                missing_or_unusable_event_order_count += 1
                continue
            event_order_eligible.append((order_value, seq, evt))

        event_order_eligible.sort(key=lambda x: (x[0], x[1]))

        if invalid_bounds:
            warnings: list[str] = ["INVALID_EVENT_ORDER_BOUNDS"]
            lines: list[str] = ["Event-order bounds were invalid; cross-band self-check summary not computed for requested window."]
            if missing_or_unusable_event_order_count > 0:
                warnings.append("EVENT_ORDER_INELIGIBLE_EVENTS_SKIPPED")
                lines.append("Transition records without usable numeric event_order were excluded from event-order selection.")
            if skipped_non_transition_count > 0:
                warnings.append("NON_TRANSITION_LEDGER_RECORDS_SKIPPED")
                lines.append("Non-transition ledger records were skipped from eligible transition selection.")
            return {
                "summary_available": False,
                "summary_mode": "CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW",
                "reason": "INVALID_EVENT_ORDER_BOUNDS",
                "window_spec": {
                    "start_event_order": requested_start,
                    "end_event_order": requested_end,
                    "max_events": requested_max_events,
                    "applied_start_event_order": None,
                    "applied_end_event_order": None,
                    "applied_event_count": 0,
                },
                "total_transition_events": total_transition_events,
                "total_event_order_eligible_events": len(event_order_eligible),
                "window_event_count": 0,
                "auditable_event_count": 0,
                "self_check_state_counts": _empty_state_counts(),
                "contradiction_flag_counts": _empty_contradiction_counts(),
                "event_type_counts": {},
                "warnings": sorted(set(warnings)),
                "explanation_lines": lines,
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if event_order_eligible:
            resolved_start = (
                event_order_eligible[0][0]
                if start_event_order is None
                else float(start_event_order)
            )
            resolved_end = (
                event_order_eligible[-1][0]
                if end_event_order is None
                else float(end_event_order)
            )
            selected_by_order = [
                (order_value, evt)
                for order_value, _, evt in event_order_eligible
                if order_value >= resolved_start and order_value <= resolved_end
            ]
        else:
            resolved_start = None
            resolved_end = None
            selected_by_order = []

        if max_events is not None:
            selected_by_order = selected_by_order[:max_events]

        selected_records = [evt for _, evt in selected_by_order]
        window_event_count = len(selected_records)
        applied_start_order = selected_by_order[0][0] if selected_by_order else None
        applied_end_order = selected_by_order[-1][0] if selected_by_order else None

        state_counts = _empty_state_counts()
        contradiction_flag_counts = _empty_contradiction_counts()
        event_type_counts: dict[str, int] = {}
        warnings: list[str] = []
        explanation_lines: list[str] = []

        unique_records: list[dict] = []
        seen_ids: set[str] = set()
        duplicate_event_id_count = 0
        for evt in selected_records:
            event_id = str(evt.get("event_id", ""))
            if event_id in seen_ids:
                duplicate_event_id_count += 1
                continue
            seen_ids.add(event_id)
            unique_records.append(evt)

        auditable_event_count = 0
        for evt in unique_records:
            event_id = str(evt.get("event_id", ""))
            event_type_norm = _norm_event_type(str(evt.get("event_type", "")))
            event_type_counts[event_type_norm] = event_type_counts.get(event_type_norm, 0) + 1

            check = self.get_transition_cross_band_self_check(event_id)
            auditable_event_count += 1

            check_state = str(check.get("self_check_state", "CROSS_BAND_UNAVAILABLE"))
            if not bool(check.get("audit_available", False)):
                check_state = "CROSS_BAND_UNAVAILABLE"
            if check_state not in state_counts:
                warnings.append("UNRECOGNIZED_SELF_CHECK_STATE")
                check_state = "CROSS_BAND_UNAVAILABLE"
            state_counts[check_state] += 1

            raw_flags = check.get("contradiction_flags", [])
            if isinstance(raw_flags, list):
                for flag in raw_flags:
                    if not isinstance(flag, str) or not flag:
                        continue
                    if flag not in contradiction_flag_counts:
                        contradiction_flag_counts[flag] = 0
                    contradiction_flag_counts[flag] += 1

        reason = "OK"
        if total_transition_events == 0:
            reason = "NO_TRANSITION_EVENTS"
            explanation_lines.append("No eligible durable transition events available for cross-band self-check event-order summary.")
        elif not event_order_eligible:
            reason = "NO_EVENT_ORDER_ELIGIBLE_EVENTS"
            explanation_lines.append("No transition events with usable event_order are available for cross-band self-check event-order summary.")
        elif window_event_count == 0:
            reason = "EMPTY_EVENT_ORDER_WINDOW_SELECTION"
            warnings.append("EMPTY_EVENT_ORDER_WINDOW_SELECTION")
            explanation_lines.append("Event-order window selection contains zero eligible transition events.")
        else:
            explanation_lines.append("Cross-band self-check event-order summary composed from per-event self-check outputs only.")

        if duplicate_event_id_count > 0:
            warnings.append("DUPLICATE_EVENT_ID_IN_LEDGER")
            explanation_lines.append(
                "Duplicate event_id records were detected in selected event-order window; counts use first occurrence per event_id."
            )
        if missing_or_unusable_event_order_count > 0:
            warnings.append("EVENT_ORDER_INELIGIBLE_EVENTS_SKIPPED")
            explanation_lines.append("Transition records without usable numeric event_order were excluded from event-order selection.")
        if skipped_non_transition_count > 0:
            warnings.append("NON_TRANSITION_LEDGER_RECORDS_SKIPPED")
            explanation_lines.append("Non-transition ledger records were skipped from eligible transition selection.")

        summary_available = True
        if reason == "NO_EVENT_ORDER_ELIGIBLE_EVENTS":
            summary_available = False

        return {
            "summary_available": summary_available,
            "summary_mode": "CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW",
            "reason": reason,
            "window_spec": {
                "start_event_order": requested_start,
                "end_event_order": requested_end,
                "max_events": requested_max_events,
                "applied_start_event_order": applied_start_order,
                "applied_end_event_order": applied_end_order,
                "applied_event_count": window_event_count,
            },
            "total_transition_events": total_transition_events,
            "total_event_order_eligible_events": len(event_order_eligible),
            "window_event_count": window_event_count,
            "auditable_event_count": auditable_event_count,
            "self_check_state_counts": state_counts,
            "contradiction_flag_counts": {k: contradiction_flag_counts[k] for k in sorted(contradiction_flag_counts.keys())},
            "event_type_counts": dict(sorted(event_type_counts.items())),
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_cross_band_self_check_window_comparator(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        index_max_events: Optional[int] = None,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        event_order_max_events: Optional[int] = None,
    ) -> dict:
        """
        Read-only comparator between index-window (v1.1) and event_order-window (v1.2)
        cross-band self-check summaries.
        """
        index_summary = self.get_cross_band_self_check_summary_window(
            start_index=start_index,
            end_index=end_index,
            max_events=index_max_events,
        )
        event_order_summary = self.get_cross_band_self_check_summary_event_order_window(
            start_event_order=start_event_order,
            end_event_order=end_event_order,
            max_events=event_order_max_events,
        )

        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        def _delta(a: int, b: int) -> int:
            # Explicit comparator direction: event_order window minus index window.
            return _as_int(b) - _as_int(a)

        def _delta_counts(
            index_counts: Optional[dict],
            event_order_counts: Optional[dict],
            known_keys: Optional[list[str]] = None,
        ) -> dict:
            a = index_counts if isinstance(index_counts, dict) else {}
            b = event_order_counts if isinstance(event_order_counts, dict) else {}
            keys = set(a.keys()) | set(b.keys())
            if known_keys:
                keys |= set(known_keys)
            return {k: _delta(a.get(k, 0), b.get(k, 0)) for k in sorted(keys)}

        index_available = bool(index_summary.get("summary_available", False))
        event_order_available = bool(event_order_summary.get("summary_available", False))

        comparison = {
            "index_window_available": index_available,
            "event_order_window_available": event_order_available,
            "total_transition_events_delta": _delta(
                index_summary.get("total_transition_events", 0),
                event_order_summary.get("total_transition_events", 0),
            ),
            "window_event_count_delta": _delta(
                index_summary.get("window_event_count", 0),
                event_order_summary.get("window_event_count", 0),
            ),
            "auditable_event_count_delta": _delta(
                index_summary.get("auditable_event_count", 0),
                event_order_summary.get("auditable_event_count", 0),
            ),
            "self_check_state_count_deltas": _delta_counts(
                index_summary.get("self_check_state_counts", {}),
                event_order_summary.get("self_check_state_counts", {}),
                known_keys=[
                    "CROSS_BAND_ALIGNMENT_OBSERVED",
                    "CROSS_BAND_CONTRADICTION_OBSERVED",
                    "CROSS_BAND_PARTIAL",
                    "CROSS_BAND_UNAVAILABLE",
                ],
            ),
            "contradiction_flag_count_deltas": _delta_counts(
                index_summary.get("contradiction_flag_counts", {}),
                event_order_summary.get("contradiction_flag_counts", {}),
                known_keys=[
                    "PRESSURE_EVENT_DIRECTION_CONTRADICTION",
                    "TOPOLOGY_EVENT_DIRECTION_CONTRADICTION",
                    "EVIDENCE_INSUFFICIENT",
                    "NO_CONTRADICTION_OBSERVED",
                ],
            ),
            "event_type_count_deltas": _delta_counts(
                index_summary.get("event_type_counts", {}),
                event_order_summary.get("event_type_counts", {}),
            ),
        }

        mismatch_flags: list[str] = []
        if not index_available:
            mismatch_flags.append("INDEX_WINDOW_UNAVAILABLE")
        if not event_order_available:
            mismatch_flags.append("EVENT_ORDER_WINDOW_UNAVAILABLE")

        if index_available and event_order_available:
            if comparison["window_event_count_delta"] != 0:
                mismatch_flags.append("WINDOW_COUNT_MISMATCH")
            if any(v != 0 for v in comparison["self_check_state_count_deltas"].values()):
                mismatch_flags.append("SELF_CHECK_STATE_MISMATCH")
            if any(v != 0 for v in comparison["contradiction_flag_count_deltas"].values()):
                mismatch_flags.append("CONTRADICTION_FLAG_MISMATCH")
            if any(v != 0 for v in comparison["event_type_count_deltas"].values()):
                mismatch_flags.append("EVENT_TYPE_MISMATCH")
            if not mismatch_flags:
                mismatch_flags.append("NO_MISMATCH_DETECTED")

        if not index_available and not event_order_available:
            reason = "BOTH_WINDOWS_UNAVAILABLE"
        elif not index_available:
            reason = "INDEX_WINDOW_UNAVAILABLE"
        elif not event_order_available:
            reason = "EVENT_ORDER_WINDOW_UNAVAILABLE"
        elif "NO_MISMATCH_DETECTED" in mismatch_flags:
            reason = "WINDOW_SUMMARIES_MATCH"
        else:
            reason = "WINDOW_SUMMARIES_DIFFER"

        warnings = sorted(
            set(
                list(index_summary.get("warnings", []))
                + list(event_order_summary.get("warnings", []))
            )
        )

        explanation_lines: list[str] = [
            "Comparator deltas use event_order_window minus index_window counts."
        ]
        if not index_available and not event_order_available:
            explanation_lines.append("Both window summaries are unavailable under requested bounds.")
        elif not index_available or not event_order_available:
            explanation_lines.append("Window availability mismatch detected between index and event_order summaries.")
        else:
            if "NO_MISMATCH_DETECTED" in mismatch_flags:
                explanation_lines.append("No count mismatches detected between index-window and event_order-window cross-band summaries.")
            else:
                explanation_lines.append("Count mismatches detected between index-window and event_order-window cross-band summaries.")
                if "WINDOW_COUNT_MISMATCH" in mismatch_flags:
                    explanation_lines.append("Selection mismatch detected: window_event_count differs between methods.")
                bucket_mismatch_flags = [
                    "SELF_CHECK_STATE_MISMATCH",
                    "CONTRADICTION_FLAG_MISMATCH",
                    "EVENT_TYPE_MISMATCH",
                ]
                if any(f in mismatch_flags for f in bucket_mismatch_flags):
                    explanation_lines.append("Bucket-count mismatch detected for one or more preserved cross-band summary groups.")

        return {
            "comparison_available": bool(index_available or event_order_available),
            "comparison_mode": "CROSS_BAND_WINDOW_COMPARATOR",
            "reason": reason,
            "request_spec": {
                "start_index": start_index,
                "end_index": end_index,
                "index_max_events": index_max_events,
                "start_event_order": start_event_order,
                "end_event_order": end_event_order,
                "event_order_max_events": event_order_max_events,
            },
            "index_window_summary": index_summary,
            "event_order_window_summary": event_order_summary,
            "comparison": comparison,
            "mismatch_flags": mismatch_flags,
            "warnings": warnings,
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_cross_band_stage_lock_audit(self) -> dict:
        """
        Stage-lock audit for the cross-band self-check band (v1.4).

        Verifies that v1.0a, v1.1, v1.2, and v1.3 cross-band APIs remain internally
        consistent, preserve bucket names and semantics, and uphold read-only guarantees.
        Read-only: no mutation, no repair, no history rewrite.
        """
        _CANONICAL_BUCKETS = [
            "CROSS_BAND_ALIGNMENT_OBSERVED",
            "CROSS_BAND_CONTRADICTION_OBSERVED",
            "CROSS_BAND_PARTIAL",
            "CROSS_BAND_UNAVAILABLE",
        ]
        _TRANSITION_TYPES = {
            "FAMILY_FISSION_V1",
            "FAMILY_REUNION_V1",
            "FAMILY_FISSION",
            "FAMILY_REUNION",
        }

        def _check_pass(name: str, reason: str, details: dict) -> dict:
            return {"check_name": name, "passed": True, "reason": reason, "details": details}

        def _check_fail(name: str, reason: str, details: dict) -> dict:
            return {"check_name": name, "passed": False, "reason": reason, "details": details}

        _CONTRACT_SURFACE = {
            "single_event_api_present": hasattr(self, "get_transition_cross_band_self_check"),
            "index_window_api_present": hasattr(self, "get_cross_band_self_check_summary_window"),
            "event_order_window_api_present": hasattr(
                self, "get_cross_band_self_check_summary_event_order_window"
            ),
            "comparator_api_present": hasattr(
                self, "get_cross_band_self_check_window_comparator"
            ),
            "bucket_surfaces": list(_CANONICAL_BUCKETS),
            "window_semantics": {
                "v1_1_index_window": "start_index_inclusive_end_index_exclusive",
                "v1_2_event_order_window": (
                    "start_event_order_inclusive_end_event_order_inclusive"
                ),
            },
            "comparator_delta_direction": "event_order_window_minus_index_window",
        }

        _REQUIRED_APIS = [
            "get_transition_cross_band_self_check",
            "get_cross_band_self_check_summary_window",
            "get_cross_band_self_check_summary_event_order_window",
            "get_cross_band_self_check_window_comparator",
        ]
        missing_apis = [name for name in _REQUIRED_APIS if not hasattr(self, name)]
        if missing_apis:
            return {
                "audit_available": False,
                "audit_mode": "CROSS_BAND_STAGE_LOCK",
                "lock_state": "CROSS_BAND_STAGE_LOCK_UNAVAILABLE",
                "reason": "REQUIRED_API_SURFACE_MISSING",
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": _CONTRACT_SURFACE,
                "warnings": [f"MISSING_API: {n}" for n in missing_apis],
                "explanation_lines": [
                    "Stage lock audit cannot proceed: required API surface missing.",
                    f"Missing: {', '.join(missing_apis)}",
                ],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        # --- Gather shared outputs (full range, no bounds) ---
        try:
            v1_1_full = self.get_cross_band_self_check_summary_window()
        except Exception as exc:
            return {
                "audit_available": False,
                "audit_mode": "CROSS_BAND_STAGE_LOCK",
                "lock_state": "CROSS_BAND_STAGE_LOCK_UNAVAILABLE",
                "reason": f"V1_1_CALL_EXCEPTION: {type(exc).__name__}",
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": _CONTRACT_SURFACE,
                "warnings": [],
                "explanation_lines": [
                    "Index-window API raised an exception during audit; stage lock unavailable."
                ],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        try:
            v1_2_full = self.get_cross_band_self_check_summary_event_order_window()
        except Exception as exc:
            return {
                "audit_available": False,
                "audit_mode": "CROSS_BAND_STAGE_LOCK",
                "lock_state": "CROSS_BAND_STAGE_LOCK_UNAVAILABLE",
                "reason": f"V1_2_CALL_EXCEPTION: {type(exc).__name__}",
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": _CONTRACT_SURFACE,
                "warnings": [],
                "explanation_lines": [
                    "Event-order-window API raised an exception during audit; stage lock unavailable."
                ],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        try:
            v1_3_full = self.get_cross_band_self_check_window_comparator()
        except Exception as exc:
            return {
                "audit_available": False,
                "audit_mode": "CROSS_BAND_STAGE_LOCK",
                "lock_state": "CROSS_BAND_STAGE_LOCK_UNAVAILABLE",
                "reason": f"V1_3_CALL_EXCEPTION: {type(exc).__name__}",
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": _CONTRACT_SURFACE,
                "warnings": [],
                "explanation_lines": [
                    "Comparator API raised an exception during audit; stage lock unavailable."
                ],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        # --- Scan ledger for transition events ---
        try:
            ledger_events = self.get_event_ledger()
        except Exception:
            ledger_events = []

        transition_events = [
            e for e in ledger_events
            if isinstance(e, dict) and e.get("event_type") in _TRANSITION_TYPES
        ]
        first_transition = transition_events[0] if transition_events else None

        # Single-event audit for checks 1 and 6
        v1_0a_result = None
        if first_transition is not None:
            try:
                v1_0a_result = self.get_transition_cross_band_self_check(
                    first_transition["event_id"]
                )
            except Exception:
                v1_0a_result = None

        # Events without pressure_snapshot (check 7); limit to first 3 for determinism
        no_pressure_events = [
            e for e in transition_events
            if isinstance(e, dict) and not e.get("pressure_snapshot")
        ][:3]

        no_pressure_results: list[tuple[str, dict]] = []
        for e in no_pressure_events:
            try:
                r = self.get_transition_cross_band_self_check(e["event_id"])
                no_pressure_results.append((e["event_id"], r))
            except Exception:
                pass

        check_results: list[dict] = []

        # ===== CHECK 1: Single-event API surface present and usable =====
        if first_transition is None:
            check_results.append(_check_pass(
                "SINGLE_EVENT_SURFACE_USABLE",
                "NO_TRANSITION_EVENTS_HONEST",
                {"note": "No transition events in ledger; not applicable but honest."},
            ))
        elif v1_0a_result is None:
            check_results.append(_check_fail(
                "SINGLE_EVENT_SURFACE_USABLE",
                "V1_0A_CALL_EXCEPTION",
                {"event_id": first_transition.get("event_id")},
            ))
        else:
            shape_ok = (
                v1_0a_result.get("audit_mode") == "CROSS_BAND_SELF_CHECK"
                and v1_0a_result.get("self_check_state") in _CANONICAL_BUCKETS
                and isinstance(v1_0a_result.get("contradiction_flags"), list)
            )
            if shape_ok:
                check_results.append(_check_pass(
                    "SINGLE_EVENT_SURFACE_USABLE",
                    "SINGLE_EVENT_API_RETURNED_VALID_SHAPE",
                    {
                        "event_id": first_transition["event_id"],
                        "self_check_state": v1_0a_result["self_check_state"],
                        "audit_mode": v1_0a_result["audit_mode"],
                    },
                ))
            else:
                check_results.append(_check_fail(
                    "SINGLE_EVENT_SURFACE_USABLE",
                    "SINGLE_EVENT_API_SHAPE_UNEXPECTED",
                    {
                        "event_id": first_transition["event_id"],
                        "audit_mode": v1_0a_result.get("audit_mode"),
                        "self_check_state": v1_0a_result.get("self_check_state"),
                    },
                ))

        # ===== CHECK 2: Full-range index-window summary consistent =====
        v1_1_mode_ok = v1_1_full.get("summary_mode") == "CROSS_BAND_SELF_CHECK_WINDOW"
        v1_1_has_counts = isinstance(v1_1_full.get("self_check_state_counts"), dict)
        if v1_1_mode_ok and v1_1_has_counts:
            check_results.append(_check_pass(
                "INDEX_WINDOW_FULL_RANGE_CONSISTENT",
                "INDEX_WINDOW_RETURNED_VALID_SHAPE",
                {
                    "summary_mode": v1_1_full.get("summary_mode"),
                    "summary_available": v1_1_full.get("summary_available"),
                    "reason": v1_1_full.get("reason"),
                },
            ))
        else:
            check_results.append(_check_fail(
                "INDEX_WINDOW_FULL_RANGE_CONSISTENT",
                "INDEX_WINDOW_SHAPE_UNEXPECTED",
                {
                    "summary_mode": v1_1_full.get("summary_mode"),
                    "has_counts": v1_1_has_counts,
                },
            ))

        # ===== CHECK 3: Comparator index side matches direct v1.1 =====
        comparator_index_side = v1_3_full.get("index_window_summary", {})
        if comparator_index_side == v1_1_full:
            check_results.append(_check_pass(
                "COMPARATOR_INDEX_SIDE_MATCHES_V1_1",
                "COMPARATOR_INDEX_SUMMARY_MATCHES_DIRECT_V1_1",
                {},
            ))
        else:
            all_keys = set(list(comparator_index_side.keys()) + list(v1_1_full.keys()))
            differing_keys = sorted(
                k for k in all_keys
                if comparator_index_side.get(k) != v1_1_full.get(k)
            )
            check_results.append(_check_fail(
                "COMPARATOR_INDEX_SIDE_MATCHES_V1_1",
                "COMPARATOR_INDEX_SUMMARY_DIFFERS_FROM_DIRECT_V1_1",
                {"differing_keys": differing_keys},
            ))

        # ===== CHECK 4: Comparator event_order side matches direct v1.2 =====
        comparator_eo_side = v1_3_full.get("event_order_window_summary", {})
        if comparator_eo_side == v1_2_full:
            check_results.append(_check_pass(
                "COMPARATOR_EVENT_ORDER_SIDE_MATCHES_V1_2",
                "COMPARATOR_EVENT_ORDER_SUMMARY_MATCHES_DIRECT_V1_2",
                {},
            ))
        else:
            all_keys = set(list(comparator_eo_side.keys()) + list(v1_2_full.keys()))
            differing_keys = sorted(
                k for k in all_keys
                if comparator_eo_side.get(k) != v1_2_full.get(k)
            )
            check_results.append(_check_fail(
                "COMPARATOR_EVENT_ORDER_SIDE_MATCHES_V1_2",
                "COMPARATOR_EVENT_ORDER_SUMMARY_DIFFERS_FROM_DIRECT_V1_2",
                {"differing_keys": differing_keys},
            ))

        # ===== CHECK 5: Bucket names and category sets preserved =====
        expected_bucket_set = set(_CANONICAL_BUCKETS)

        def _bucket_drift(counts: dict) -> tuple:
            actual = set(counts.keys()) if isinstance(counts, dict) else set()
            return actual - expected_bucket_set, expected_bucket_set - actual

        v1_1_extra, v1_1_missing = _bucket_drift(v1_1_full.get("self_check_state_counts", {}))
        v1_2_extra, v1_2_missing = _bucket_drift(v1_2_full.get("self_check_state_counts", {}))

        if not v1_1_extra and not v1_1_missing and not v1_2_extra and not v1_2_missing:
            check_results.append(_check_pass(
                "BUCKET_NAMES_PRESERVED",
                "CANONICAL_BUCKET_NAMES_PRESENT_IN_ALL_OUTPUTS",
                {"canonical_buckets": list(_CANONICAL_BUCKETS)},
            ))
        else:
            drift_details: dict = {}
            if v1_1_extra or v1_1_missing:
                drift_details["v1_1_extra_keys"] = sorted(v1_1_extra)
                drift_details["v1_1_missing_keys"] = sorted(v1_1_missing)
            if v1_2_extra or v1_2_missing:
                drift_details["v1_2_extra_keys"] = sorted(v1_2_extra)
                drift_details["v1_2_missing_keys"] = sorted(v1_2_missing)
            check_results.append(_check_fail(
                "BUCKET_NAMES_PRESERVED",
                "BUCKET_NAME_DRIFT_DETECTED",
                drift_details,
            ))

        # ===== CHECK 6: Read-only guardrail flags remain false =====
        _GUARDRAIL_FIELDS = [
            "lineage_mutation_performed",
            "event_creation_performed",
            "history_rewrite_performed",
        ]
        audited_outputs: list[tuple[str, dict]] = [
            ("v1_1_full", v1_1_full),
            ("v1_2_full", v1_2_full),
            ("v1_3_full", v1_3_full),
        ]
        if v1_0a_result is not None:
            audited_outputs.append(("v1_0a_result", v1_0a_result))

        guardrail_violations = [
            f"{name}.{field}"
            for name, output in audited_outputs
            for field in _GUARDRAIL_FIELDS
            if output.get(field) is True
        ]
        if not guardrail_violations:
            check_results.append(_check_pass(
                "READ_ONLY_GUARDRAILS_FALSE",
                "ALL_GUARDRAIL_FLAGS_FALSE",
                {"checked_outputs": [n for n, _ in audited_outputs]},
            ))
        else:
            check_results.append(_check_fail(
                "READ_ONLY_GUARDRAILS_FALSE",
                "GUARDRAIL_FLAG_VIOLATION_DETECTED",
                {"violations": guardrail_violations},
            ))

        # ===== CHECK 7: Known unavailable cases remain unavailable honestly =====
        _HARDENED_STATES = {
            "CROSS_BAND_ALIGNMENT_OBSERVED",
            "CROSS_BAND_CONTRADICTION_OBSERVED",
        }
        if not no_pressure_events:
            check_results.append(_check_pass(
                "UNAVAILABLE_CASES_REMAIN_UNAVAILABLE",
                "NO_UNAVAILABLE_CANDIDATES_IN_LEDGER",
                {"note": "No transition events without pressure_snapshot found; not applicable."},
            ))
        else:
            hardened = [
                {"event_id": eid, "unexpected_state": r.get("self_check_state")}
                for eid, r in no_pressure_results
                if r.get("self_check_state") in _HARDENED_STATES
            ]
            if not hardened:
                check_results.append(_check_pass(
                    "UNAVAILABLE_CASES_REMAIN_UNAVAILABLE",
                    "UNAVAILABLE_CASES_HONEST",
                    {
                        "events_checked": [e["event_id"] for e in no_pressure_events],
                        "states_observed": [
                            r.get("self_check_state") for _, r in no_pressure_results
                        ],
                    },
                ))
            else:
                check_results.append(_check_fail(
                    "UNAVAILABLE_CASES_REMAIN_UNAVAILABLE",
                    "UNAVAILABLE_CASE_HARDENED_WITHOUT_EVIDENCE",
                    {"violations": hardened},
                ))

        # ===== CHECK 8: Comparator delta direction is event_order_window - index_window =====
        comp_block = v1_3_full.get("comparison", {})
        idx_counts = (
            v1_3_full.get("index_window_summary", {}).get("self_check_state_counts", {})
        )
        eo_counts = (
            v1_3_full.get("event_order_window_summary", {}).get("self_check_state_counts", {})
        )
        reported_deltas = comp_block.get("self_check_state_count_deltas", {})

        bucket_delta_details: dict = {}
        delta_direction_ok = True
        for k in _CANONICAL_BUCKETS:
            expected_delta = (eo_counts.get(k) or 0) - (idx_counts.get(k) or 0)
            reported_delta = reported_deltas.get(k)
            match = (expected_delta == reported_delta)
            bucket_delta_details[k] = {
                "index_count": idx_counts.get(k, 0),
                "event_order_count": eo_counts.get(k, 0),
                "expected_delta": expected_delta,
                "reported_delta": reported_delta,
                "match": match,
            }
            if not match:
                delta_direction_ok = False

        if delta_direction_ok:
            check_results.append(_check_pass(
                "COMPARATOR_DELTA_DIRECTION_CORRECT",
                "DELTA_DIRECTION_MATCHES_EVENT_ORDER_MINUS_INDEX",
                {
                    "direction": "event_order_window_minus_index_window",
                    "bucket_deltas": bucket_delta_details,
                },
            ))
        else:
            wrong_keys = sorted(k for k, v in bucket_delta_details.items() if not v["match"])
            check_results.append(_check_fail(
                "COMPARATOR_DELTA_DIRECTION_CORRECT",
                "DELTA_DIRECTION_MISMATCH_DETECTED",
                {"wrong_keys": wrong_keys, "bucket_deltas": bucket_delta_details},
            ))

        # --- Aggregate ---
        checks_run = len(check_results)
        checks_passed = sum(1 for c in check_results if c["passed"])
        checks_failed = checks_run - checks_passed

        if checks_failed == 0:
            lock_state = "CROSS_BAND_STAGE_LOCKED"
            reason = "ALL_CONSISTENCY_CHECKS_PASSED"
        else:
            lock_state = "CROSS_BAND_STAGE_LOCK_INCONSISTENT"
            reason = "CONSISTENCY_CHECK_FAILED"

        all_warnings: list[str] = []
        for _, output in audited_outputs:
            for w in output.get("warnings", []):
                if w not in all_warnings:
                    all_warnings.append(w)

        explanation_lines = [
            "Cross-band stage lock audit v1.4.",
            f"Checks run: {checks_run}. Passed: {checks_passed}. Failed: {checks_failed}.",
        ]
        if lock_state == "CROSS_BAND_STAGE_LOCKED":
            explanation_lines.append(
                "Cross-band band is stage-locked: all required consistency checks pass."
            )
        else:
            failed_names = [c["check_name"] for c in check_results if not c["passed"]]
            explanation_lines.append(
                "Stage lock inconsistency detected: one or more required checks failed."
            )
            explanation_lines.append(f"Failed checks: {', '.join(failed_names)}.")

        return {
            "audit_available": True,
            "audit_mode": "CROSS_BAND_STAGE_LOCK",
            "lock_state": lock_state,
            "reason": reason,
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "check_results": check_results,
            "contract_surface": _CONTRACT_SURFACE,
            "warnings": sorted(set(all_warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_transition_pressure_capture_audit(self, event_id: str) -> dict:
        """
        Audits structural integrity of an event-local pressure_snapshot block.
        Read-only: no mutation, no repair, no history rewrite.
        """
        evt, duplicate_count = self._get_ledger_event_by_id(event_id)
        if evt is None:
            return {
                "event_id": event_id,
                "found": False,
                "audit_available": False,
                "audit_state": "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE",
                "reason": "EVENT_NOT_FOUND",
                "event_type": None,
                "participant_family_ids": [],
                "pressure_snapshot_present": False,
                "structural_validity": {"ok": False, "issues": ["EVENT_NOT_FOUND"]},
                "metadata_consistency": {"ok": False, "issues": ["EVENT_NOT_FOUND"]},
                "payload_consistency": {"ok": False, "issues": ["EVENT_NOT_FOUND"]},
                "reader_consistency": {"ok": False, "issues": ["EVENT_NOT_FOUND"]},
                "warnings": ["EVENT_NOT_FOUND"],
                "explanation_lines": ["Event ID is not present in durable ledger; capture audit unavailable."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        source_ids = sorted([x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x])
        successor_ids = sorted([x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x])
        participant_ids = sorted(set(source_ids + successor_ids))

        pressure_snapshot = evt.get("pressure_snapshot")
        if not isinstance(pressure_snapshot, dict):
            warnings: list[str] = []
            if duplicate_count > 1:
                warnings.append("DUPLICATE_EVENT_ID_IN_LEDGER")
            warnings.append("EVENT_PRESSURE_SNAPSHOT_NOT_STORED")
            return {
                "event_id": event_id,
                "found": True,
                "audit_available": False,
                "audit_state": "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE",
                "reason": "PRESSURE_SNAPSHOT_NOT_STORED",
                "event_type": evt.get("event_type"),
                "participant_family_ids": participant_ids,
                "pressure_snapshot_present": False,
                "structural_validity": {"ok": False, "issues": ["PRESSURE_SNAPSHOT_NOT_STORED"]},
                "metadata_consistency": {"ok": False, "issues": ["PRESSURE_SNAPSHOT_NOT_STORED"]},
                "payload_consistency": {"ok": False, "issues": ["PRESSURE_SNAPSHOT_NOT_STORED"]},
                "reader_consistency": {"ok": False, "issues": ["PRESSURE_SNAPSHOT_NOT_STORED"]},
                "warnings": sorted(set(warnings)),
                "explanation_lines": ["Event has no pressure_snapshot block; capture audit unavailable."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        known_reasons = {
            "PRESSURE_CAPTURE_FULL",
            "PRESSURE_CAPTURE_PARTIAL",
            "PRESSURE_CAPTURE_FAILED",
        }

        def _status_known(status: str) -> bool:
            static_statuses = {
                "PRESSURE_CAPTURED",
                "PRESSURE_UNAVAILABLE",
                "PRESSURE_CAPTURE_OUTPUT_INVALID",
                "PRESSURE_STAGE_COLLISION",
            }
            if status in static_statuses:
                return True
            if status.startswith("PRESSURE_CAPTURE_EXCEPTION:"):
                return True
            return False

        structural_issues: list[str] = []
        metadata_issues: list[str] = []
        payload_issues: list[str] = []
        reader_issues: list[str] = []
        warnings: list[str] = []
        explanation_lines: list[str] = []

        if duplicate_count > 1:
            warnings.append("DUPLICATE_EVENT_ID_IN_LEDGER")

        required_fields = [
            "pre_event_pressure",
            "post_event_pressure",
            "capture_attempted",
            "capture_succeeded",
            "capture_mode",
            "capture_reason",
            "pre_capture_status_by_family",
            "post_capture_status_by_family",
        ]
        for field_name in required_fields:
            if field_name not in pressure_snapshot:
                structural_issues.append(f"PRESSURE_SNAPSHOT_MISSING_FIELD:{field_name}")

        pre_payload = pressure_snapshot.get("pre_event_pressure")
        post_payload = pressure_snapshot.get("post_event_pressure")
        capture_attempted = pressure_snapshot.get("capture_attempted")
        capture_succeeded = pressure_snapshot.get("capture_succeeded")
        capture_mode = pressure_snapshot.get("capture_mode")
        capture_reason = pressure_snapshot.get("capture_reason")
        pre_status_map = pressure_snapshot.get("pre_capture_status_by_family")
        post_status_map = pressure_snapshot.get("post_capture_status_by_family")

        pre_present = isinstance(pre_payload, dict) and bool(pre_payload)
        post_present = isinstance(post_payload, dict) and bool(post_payload)

        if pre_payload is not None and not isinstance(pre_payload, dict):
            structural_issues.append("PRE_EVENT_PRESSURE_NOT_DICT_OR_NULL")
        if post_payload is not None and not isinstance(post_payload, dict):
            structural_issues.append("POST_EVENT_PRESSURE_NOT_DICT_OR_NULL")
        if not isinstance(capture_attempted, bool):
            structural_issues.append("CAPTURE_ATTEMPTED_NOT_BOOL")
        if not isinstance(capture_succeeded, bool):
            structural_issues.append("CAPTURE_SUCCEEDED_NOT_BOOL")
        if not isinstance(capture_mode, str):
            structural_issues.append("CAPTURE_MODE_NOT_STRING")
        elif capture_mode != "EVENT_WRITE_TIME":
            metadata_issues.append("CAPTURE_MODE_UNRECOGNIZED")
        if not isinstance(capture_reason, str):
            structural_issues.append("CAPTURE_REASON_NOT_STRING")
        elif capture_reason not in known_reasons:
            metadata_issues.append("CAPTURE_REASON_UNRECOGNIZED")

        if not isinstance(pre_status_map, dict):
            structural_issues.append("PRE_CAPTURE_STATUS_MAP_NOT_DICT")
            pre_status_map = {}
        if not isinstance(post_status_map, dict):
            structural_issues.append("POST_CAPTURE_STATUS_MAP_NOT_DICT")
            post_status_map = {}

        pre_status_keys = sorted([str(k) for k in pre_status_map.keys()])
        post_status_keys = sorted([str(k) for k in post_status_map.keys()])
        expected_pre_keys = sorted(source_ids)
        expected_post_keys = sorted(successor_ids)
        if sorted(pre_status_keys) != expected_pre_keys:
            metadata_issues.append("PRE_CAPTURE_STATUS_MAP_KEY_MISMATCH")
        if sorted(post_status_keys) != expected_post_keys:
            metadata_issues.append("POST_CAPTURE_STATUS_MAP_KEY_MISMATCH")
        for status in [str(v) for v in pre_status_map.values()]:
            if not _status_known(status):
                metadata_issues.append("PRE_CAPTURE_STATUS_VALUE_UNRECOGNIZED")
                break
        for status in [str(v) for v in post_status_map.values()]:
            if not _status_known(status):
                metadata_issues.append("POST_CAPTURE_STATUS_VALUE_UNRECOGNIZED")
                break

        if isinstance(pre_payload, dict) and pre_payload:
            pre_family_ids = pre_payload.get("family_ids")
            pre_by_id = pre_payload.get("family_pressure_by_id")
            if not isinstance(pre_family_ids, list):
                payload_issues.append("PRE_EVENT_PRESSURE_FAMILY_IDS_NOT_LIST")
            if not isinstance(pre_by_id, dict):
                payload_issues.append("PRE_EVENT_PRESSURE_BY_ID_NOT_DICT")
            if isinstance(pre_family_ids, list) and isinstance(pre_by_id, dict):
                pre_ids_norm = sorted([str(x) for x in pre_family_ids if isinstance(x, str) and x])
                pre_keys = sorted([str(k) for k in pre_by_id.keys()])
                if pre_ids_norm != pre_keys:
                    payload_issues.append("PRE_EVENT_PRESSURE_IDS_MISMATCH")
                if any(x not in source_ids for x in pre_keys):
                    payload_issues.append("PRE_EVENT_PRESSURE_FAMILY_NOT_IN_SOURCE_IDS")
                for value in pre_by_id.values():
                    if not isinstance(value, dict) or not value:
                        payload_issues.append("PRE_EVENT_PRESSURE_VALUE_INVALID")
                        break

        if isinstance(post_payload, dict) and post_payload:
            post_family_ids = post_payload.get("family_ids")
            post_by_id = post_payload.get("family_pressure_by_id")
            if not isinstance(post_family_ids, list):
                payload_issues.append("POST_EVENT_PRESSURE_FAMILY_IDS_NOT_LIST")
            if not isinstance(post_by_id, dict):
                payload_issues.append("POST_EVENT_PRESSURE_BY_ID_NOT_DICT")
            if isinstance(post_family_ids, list) and isinstance(post_by_id, dict):
                post_ids_norm = sorted([str(x) for x in post_family_ids if isinstance(x, str) and x])
                post_keys = sorted([str(k) for k in post_by_id.keys()])
                if post_ids_norm != post_keys:
                    payload_issues.append("POST_EVENT_PRESSURE_IDS_MISMATCH")
                if any(x not in successor_ids for x in post_keys):
                    payload_issues.append("POST_EVENT_PRESSURE_FAMILY_NOT_IN_SUCCESSOR_IDS")
                for value in post_by_id.values():
                    if not isinstance(value, dict) or not value:
                        payload_issues.append("POST_EVENT_PRESSURE_VALUE_INVALID")
                        break

        if capture_reason == "PRESSURE_CAPTURE_FULL":
            if not pre_present or not post_present:
                metadata_issues.append("CAPTURE_REASON_FULL_REQUIRES_BOTH_SIDES")
            if capture_succeeded is not True:
                metadata_issues.append("CAPTURE_REASON_FULL_REQUIRES_CAPTURE_SUCCEEDED_TRUE")
        elif capture_reason == "PRESSURE_CAPTURE_PARTIAL":
            if not (pre_present or post_present):
                metadata_issues.append("CAPTURE_REASON_PARTIAL_REQUIRES_AT_LEAST_ONE_SIDE")
            if pre_present and post_present:
                metadata_issues.append("CAPTURE_REASON_PARTIAL_DISALLOWS_BOTH_SIDES")
            if capture_succeeded is not True:
                metadata_issues.append("CAPTURE_REASON_PARTIAL_REQUIRES_CAPTURE_SUCCEEDED_TRUE")
        elif capture_reason == "PRESSURE_CAPTURE_FAILED":
            if pre_present or post_present:
                metadata_issues.append("CAPTURE_REASON_FAILED_DISALLOWS_PAYLOAD")
            if capture_succeeded is not False:
                metadata_issues.append("CAPTURE_REASON_FAILED_REQUIRES_CAPTURE_SUCCEEDED_FALSE")

        if capture_attempted is False and (pre_present or post_present):
            metadata_issues.append("CAPTURE_ATTEMPTED_FALSE_WITH_PAYLOAD")

        snapshot = self.get_transition_pressure_snapshot(event_id)
        if not bool(snapshot.get("found", False)):
            reader_issues.append("SNAPSHOT_READER_EVENT_LOOKUP_MISMATCH")
        raw_pre = pre_present
        raw_post = post_present
        reader_pre = bool(snapshot.get("evidence_flags", {}).get("pre_event_pressure_recoverable", False))
        reader_post = bool(snapshot.get("evidence_flags", {}).get("post_event_pressure_recoverable", False))
        if reader_pre != raw_pre:
            reader_issues.append("SNAPSHOT_READER_PRE_RECOVERABILITY_MISMATCH")
        if reader_post != raw_post:
            reader_issues.append("SNAPSHOT_READER_POST_RECOVERABILITY_MISMATCH")
        reader_snapshot_available = bool(snapshot.get("snapshot_available", False))
        if reader_snapshot_available != bool(raw_pre or raw_post):
            reader_issues.append("SNAPSHOT_READER_AVAILABILITY_MISMATCH")
        if raw_pre and snapshot.get("pre_event_pressure") is None:
            reader_issues.append("SNAPSHOT_READER_PRE_PAYLOAD_MISSING")
        if (not raw_pre) and snapshot.get("pre_event_pressure") is not None:
            reader_issues.append("SNAPSHOT_READER_PRE_PAYLOAD_OVERCLAIM")
        if raw_post and snapshot.get("post_event_pressure") is None:
            reader_issues.append("SNAPSHOT_READER_POST_PAYLOAD_MISSING")
        if (not raw_post) and snapshot.get("post_event_pressure") is not None:
            reader_issues.append("SNAPSHOT_READER_POST_PAYLOAD_OVERCLAIM")

        structural_ok = len(structural_issues) == 0
        metadata_ok = len(metadata_issues) == 0
        payload_ok = len(payload_issues) == 0
        reader_ok = len(reader_issues) == 0
        audit_ok = structural_ok and metadata_ok and payload_ok and reader_ok

        if audit_ok:
            audit_state = "PRESSURE_CAPTURE_AUDIT_VALID"
            reason = "PRESSURE_CAPTURE_AUDIT_PASSED"
            explanation_lines.append("pressure_snapshot block is structurally valid and reader-consistent.")
        else:
            audit_state = "PRESSURE_CAPTURE_AUDIT_INVALID"
            reason = "PRESSURE_CAPTURE_AUDIT_FAILED"
            explanation_lines.append("pressure_snapshot block has integrity mismatches.")

        warnings.extend(structural_issues)
        warnings.extend(metadata_issues)
        warnings.extend(payload_issues)
        warnings.extend(reader_issues)

        return {
            "event_id": event_id,
            "found": True,
            "audit_available": True,
            "audit_state": audit_state,
            "reason": reason,
            "event_type": evt.get("event_type"),
            "participant_family_ids": participant_ids,
            "pressure_snapshot_present": True,
            "structural_validity": {"ok": structural_ok, "issues": sorted(set(structural_issues))},
            "metadata_consistency": {"ok": metadata_ok, "issues": sorted(set(metadata_issues))},
            "payload_consistency": {"ok": payload_ok, "issues": sorted(set(payload_issues))},
            "reader_consistency": {"ok": reader_ok, "issues": sorted(set(reader_issues))},
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_pressure_capture_quality_summary(self) -> dict:
        """
        Read-only cross-event summary of pressure capture quality over durable transition events.
        Uses existing snapshot/audit APIs and does not mutate ledger or lineage state.
        """
        return self._get_pressure_capture_quality_summary_for_events(
            summary_mode="LEDGER_READ_ONLY",
            total_transition_events_override=None,
            window_spec=None,
            reason="OK",
            selected_transition_records=None,
        )

    def _select_eligible_transition_events(self, ledger_events: list[dict]) -> tuple[list[dict], int]:
        transition_records: list[dict] = []
        skipped_non_transition_count = 0
        for evt in ledger_events:
            if not isinstance(evt, dict):
                skipped_non_transition_count += 1
                continue
            event_id = str(evt.get("event_id", ""))
            event_type = evt.get("event_type")
            source_ids = [x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x]
            successor_ids = [x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x]
            if not event_id or not isinstance(event_type, str) or not event_type:
                skipped_non_transition_count += 1
                continue
            if not source_ids and not successor_ids:
                skipped_non_transition_count += 1
                continue
            transition_records.append(evt)
        return transition_records, skipped_non_transition_count

    def _get_pressure_capture_quality_summary_for_events(
        self,
        *,
        summary_mode: str,
        total_transition_events_override: Optional[int],
        window_spec: Optional[dict],
        reason: str,
        selected_transition_records: Optional[list[dict]],
    ) -> dict:
        """
        Shared summary implementation for v1.4 and v1.5.
        Read-only and deterministic; no mutation, no repair, no retrofit.
        """
        ledger_events = self.get_event_ledger()
        transition_records, skipped_non_transition_count = self._select_eligible_transition_events(ledger_events)
        if selected_transition_records is None:
            selected_transition_records = transition_records

        unique_events: list[dict] = []
        seen_ids: set[str] = set()
        duplicate_event_id_count = 0
        for evt in selected_transition_records:
            event_id = str(evt.get("event_id", ""))
            if event_id in seen_ids:
                duplicate_event_id_count += 1
                continue
            seen_ids.add(event_id)
            unique_events.append(evt)

        known_capture_reasons = {
            "PRESSURE_CAPTURE_FULL",
            "PRESSURE_CAPTURE_PARTIAL",
            "PRESSURE_CAPTURE_FAILED",
        }

        def _norm_event_type(event_type: str) -> str:
            if event_type.startswith("FAMILY_FISSION"):
                return "FAMILY_FISSION"
            if event_type.startswith("FAMILY_REUNION"):
                return "FAMILY_REUNION"
            return event_type

        def _empty_audit_state_counts() -> dict:
            return {
                "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
            }

        def _empty_capture_reason_counts() -> dict:
            return {
                "PRESSURE_CAPTURE_FULL": 0,
                "PRESSURE_CAPTURE_PARTIAL": 0,
                "PRESSURE_CAPTURE_FAILED": 0,
                "UNRECOGNIZED_CAPTURE_REASON": 0,
            }

        def _empty_recoverability_counts() -> dict:
            return {
                "FULLY_RECOVERABLE": 0,
                "PARTIALLY_RECOVERABLE": 0,
                "UNRECOVERABLE": 0,
            }

        audit_state_counts = _empty_audit_state_counts()
        capture_reason_counts = _empty_capture_reason_counts()
        recoverability_counts = _empty_recoverability_counts()
        event_type_counts: dict[str, int] = {}
        event_type_breakdown: dict[str, dict] = {}

        pressure_snapshot_present_count = 0
        pressure_snapshot_missing_count = 0

        for evt in unique_events:
            event_id = str(evt.get("event_id", ""))
            event_type_norm = _norm_event_type(str(evt.get("event_type", "")))
            event_type_counts[event_type_norm] = event_type_counts.get(event_type_norm, 0) + 1
            if event_type_norm not in event_type_breakdown:
                event_type_breakdown[event_type_norm] = {
                    "total": 0,
                    "pressure_snapshot_present": 0,
                    "pressure_snapshot_missing": 0,
                    "audit_state_counts": _empty_audit_state_counts(),
                    "capture_reason_counts": _empty_capture_reason_counts(),
                    "recoverability_counts": _empty_recoverability_counts(),
                }
            b = event_type_breakdown[event_type_norm]
            b["total"] += 1

            snapshot_present = isinstance(evt.get("pressure_snapshot"), dict)
            if snapshot_present:
                pressure_snapshot_present_count += 1
                b["pressure_snapshot_present"] += 1
                capture_reason = evt.get("pressure_snapshot", {}).get("capture_reason")
                if isinstance(capture_reason, str) and capture_reason in known_capture_reasons:
                    capture_reason_counts[capture_reason] += 1
                    b["capture_reason_counts"][capture_reason] += 1
                else:
                    capture_reason_counts["UNRECOGNIZED_CAPTURE_REASON"] += 1
                    b["capture_reason_counts"]["UNRECOGNIZED_CAPTURE_REASON"] += 1
            else:
                pressure_snapshot_missing_count += 1
                b["pressure_snapshot_missing"] += 1

            audit = self.get_transition_pressure_capture_audit(event_id)
            audit_state = str(audit.get("audit_state", "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE"))
            if audit_state not in audit_state_counts:
                audit_state = "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE"
            audit_state_counts[audit_state] += 1
            b["audit_state_counts"][audit_state] += 1

            snapshot = self.get_transition_pressure_snapshot(event_id)
            pre_recoverable = bool(snapshot.get("evidence_flags", {}).get("pre_event_pressure_recoverable", False))
            post_recoverable = bool(snapshot.get("evidence_flags", {}).get("post_event_pressure_recoverable", False))
            if pre_recoverable and post_recoverable:
                recoverability_key = "FULLY_RECOVERABLE"
            elif pre_recoverable or post_recoverable:
                recoverability_key = "PARTIALLY_RECOVERABLE"
            else:
                recoverability_key = "UNRECOVERABLE"
            recoverability_counts[recoverability_key] += 1
            b["recoverability_counts"][recoverability_key] += 1

        warnings: list[str] = []
        explanation_lines: list[str] = []
        if duplicate_event_id_count > 0:
            warnings.append("DUPLICATE_EVENT_ID_IN_LEDGER")
            explanation_lines.append(
                "Duplicate event_id records were detected; summary counts use first occurrence per event_id."
            )
        if skipped_non_transition_count > 0:
            warnings.append("NON_TRANSITION_LEDGER_RECORDS_SKIPPED")
            explanation_lines.append("Non-transition ledger records were skipped from capture quality summary.")
        if not unique_events:
            explanation_lines.append("No durable transition events available for pressure capture quality summary.")
        else:
            explanation_lines.append("Capture quality summary computed from durable transition events via read-only audit/snapshot APIs.")

        total_transition_events = (
            len(unique_events) if total_transition_events_override is None else int(total_transition_events_override)
        )

        out = {
            "summary_available": True,
            "summary_mode": summary_mode,
            "reason": reason,
            "total_transition_events": total_transition_events,
            "auditable_event_count": len(unique_events),
            "pressure_snapshot_present_count": pressure_snapshot_present_count,
            "pressure_snapshot_missing_count": pressure_snapshot_missing_count,
            "audit_state_counts": audit_state_counts,
            "capture_reason_counts": capture_reason_counts,
            "recoverability_counts": recoverability_counts,
            "event_type_counts": dict(sorted(event_type_counts.items())),
            "event_type_breakdown": {k: event_type_breakdown[k] for k in sorted(event_type_breakdown.keys())},
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }
        if window_spec is not None:
            out["window_spec"] = window_spec
            out["window_event_count"] = int(window_spec.get("applied_event_count", 0))
        return out

    def get_pressure_capture_quality_summary_window(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Read-only windowed capture quality summary over eligible durable transition events.
        Index behavior:
        - start_index: inclusive
        - end_index: exclusive
        - max_events: truncates window deterministically after bound resolution
        """
        def _is_valid_bound(v: Optional[int]) -> bool:
            return v is None or isinstance(v, int)

        invalid_bounds = (
            (not _is_valid_bound(start_index))
            or (not _is_valid_bound(end_index))
            or (not _is_valid_bound(max_events))
            or (isinstance(start_index, int) and start_index < 0)
            or (isinstance(end_index, int) and end_index < 0)
            or (isinstance(max_events, int) and max_events < 0)
            or (
                isinstance(start_index, int)
                and isinstance(end_index, int)
                and end_index < start_index
            )
        )

        ledger_events = self.get_event_ledger()
        transition_records, skipped_non_transition_count = self._select_eligible_transition_events(ledger_events)

        requested_start = start_index
        requested_end = end_index
        requested_max_events = max_events

        if invalid_bounds:
            window_spec = {
                "start_index": requested_start,
                "end_index": requested_end,
                "max_events": requested_max_events,
                "applied_start_index": None,
                "applied_end_index": None,
                "applied_event_count": 0,
            }
            out = self._get_pressure_capture_quality_summary_for_events(
                summary_mode="LEDGER_READ_ONLY_WINDOWED",
                total_transition_events_override=len(transition_records),
                window_spec=window_spec,
                reason="INVALID_WINDOW_BOUNDS",
                selected_transition_records=[],
            )
            out["summary_available"] = False
            out["warnings"] = sorted(set(out.get("warnings", []) + ["INVALID_WINDOW_BOUNDS"]))
            lines = [
                line
                for line in out.get("explanation_lines", [])
                if line != "No durable transition events available for pressure capture quality summary."
            ]
            lines.append("Window bounds were invalid; summary not computed for requested slice.")
            out["explanation_lines"] = lines
            if skipped_non_transition_count > 0 and "NON_TRANSITION_LEDGER_RECORDS_SKIPPED" not in out["warnings"]:
                out["warnings"].append("NON_TRANSITION_LEDGER_RECORDS_SKIPPED")
                out["warnings"] = sorted(set(out["warnings"]))
            return out

        resolved_start = 0 if start_index is None else start_index
        resolved_end = len(transition_records) if end_index is None else end_index
        sliced_records = transition_records[resolved_start:resolved_end]
        if max_events is not None:
            sliced_records = sliced_records[:max_events]
        applied_count = len(sliced_records)
        applied_start = resolved_start
        applied_end = resolved_start + applied_count

        window_spec = {
            "start_index": requested_start,
            "end_index": requested_end,
            "max_events": requested_max_events,
            "applied_start_index": applied_start,
            "applied_end_index": applied_end,
            "applied_event_count": applied_count,
        }

        reason = "OK"
        if not transition_records:
            reason = "NO_TRANSITION_EVENTS"
        elif applied_count == 0:
            reason = "EMPTY_WINDOW_SELECTION"

        out = self._get_pressure_capture_quality_summary_for_events(
            summary_mode="LEDGER_READ_ONLY_WINDOWED",
            total_transition_events_override=len(transition_records),
            window_spec=window_spec,
            reason=reason,
            selected_transition_records=sliced_records,
        )
        if applied_count == 0:
            out["warnings"] = sorted(set(out.get("warnings", []) + ["EMPTY_WINDOW_SELECTION"]))
            lines = [
                line
                for line in out.get("explanation_lines", [])
                if line != "No durable transition events available for pressure capture quality summary."
            ]
            lines.append("Window selection contains zero eligible transition events.")
            out["explanation_lines"] = lines
        return out

    def get_pressure_capture_quality_summary_event_order_window(
        self,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Read-only capture quality summary over eligible transition events selected by event_order bounds.
        Event-order behavior:
        - start_event_order: inclusive
        - end_event_order: inclusive
        - max_events: truncates deterministically after event_order filtering
        - deterministic tie behavior: order by (event_order asc, ledger transition sequence asc)
        """
        def _is_valid_order_bound(v: Optional[float]) -> bool:
            if v is None:
                return True
            if isinstance(v, bool):
                return False
            if isinstance(v, (int, float)):
                return math.isfinite(float(v))
            return False

        def _is_valid_max_events(v: Optional[int]) -> bool:
            if v is None:
                return True
            if isinstance(v, bool):
                return False
            return isinstance(v, int)

        invalid_bounds = (
            (not _is_valid_order_bound(start_event_order))
            or (not _is_valid_order_bound(end_event_order))
            or (not _is_valid_max_events(max_events))
            or (isinstance(max_events, int) and max_events < 0)
            or (
                isinstance(start_event_order, (int, float))
                and isinstance(end_event_order, (int, float))
                and float(end_event_order) < float(start_event_order)
            )
        )

        ledger_events = self.get_event_ledger()
        transition_records, _ = self._select_eligible_transition_events(ledger_events)

        requested_start = start_event_order
        requested_end = end_event_order
        requested_max_events = max_events

        event_order_eligible: list[tuple[float, int, dict]] = []
        missing_or_unusable_event_order_count = 0
        for seq, evt in enumerate(transition_records):
            raw_order = evt.get("event_order")
            if isinstance(raw_order, bool) or not isinstance(raw_order, (int, float)):
                missing_or_unusable_event_order_count += 1
                continue
            order_value = float(raw_order)
            if not math.isfinite(order_value):
                missing_or_unusable_event_order_count += 1
                continue
            event_order_eligible.append((order_value, seq, evt))

        event_order_eligible.sort(key=lambda x: (x[0], x[1]))

        if invalid_bounds:
            window_spec = {
                "start_event_order": requested_start,
                "end_event_order": requested_end,
                "max_events": requested_max_events,
                "applied_start_event_order": None,
                "applied_end_event_order": None,
                "applied_event_count": 0,
            }
            out = self._get_pressure_capture_quality_summary_for_events(
                summary_mode="LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED",
                total_transition_events_override=len(transition_records),
                window_spec=window_spec,
                reason="INVALID_EVENT_ORDER_BOUNDS",
                selected_transition_records=[],
            )
            out["summary_available"] = False
            out["total_event_order_eligible_events"] = len(event_order_eligible)
            warnings = list(out.get("warnings", []))
            warnings.append("INVALID_EVENT_ORDER_BOUNDS")
            if missing_or_unusable_event_order_count > 0:
                warnings.append("EVENT_ORDER_INELIGIBLE_EVENTS_SKIPPED")
            out["warnings"] = sorted(set(warnings))
            out["explanation_lines"] = [
                "Event-order bounds were invalid; summary not computed for requested event_order window."
            ]
            return out

        if event_order_eligible:
            resolved_start = (
                event_order_eligible[0][0]
                if start_event_order is None
                else float(start_event_order)
            )
            resolved_end = (
                event_order_eligible[-1][0]
                if end_event_order is None
                else float(end_event_order)
            )
            selected_by_order = [
                (order_value, evt)
                for order_value, _, evt in event_order_eligible
                if order_value >= resolved_start and order_value <= resolved_end
            ]
        else:
            resolved_start = None
            resolved_end = None
            selected_by_order = []

        if max_events is not None:
            selected_by_order = selected_by_order[:max_events]

        selected_records = [evt for _, evt in selected_by_order]
        applied_count = len(selected_records)
        applied_start_order = selected_by_order[0][0] if selected_by_order else None
        applied_end_order = selected_by_order[-1][0] if selected_by_order else None

        window_spec = {
            "start_event_order": requested_start,
            "end_event_order": requested_end,
            "max_events": requested_max_events,
            "applied_start_event_order": applied_start_order,
            "applied_end_event_order": applied_end_order,
            "applied_event_count": applied_count,
        }

        reason = "OK"
        if not transition_records:
            reason = "NO_TRANSITION_EVENTS"
        elif not event_order_eligible:
            reason = "NO_EVENT_ORDER_ELIGIBLE_EVENTS"
        elif applied_count == 0:
            reason = "EMPTY_EVENT_ORDER_WINDOW_SELECTION"

        out = self._get_pressure_capture_quality_summary_for_events(
            summary_mode="LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED",
            total_transition_events_override=len(transition_records),
            window_spec=window_spec,
            reason=reason,
            selected_transition_records=selected_records,
        )
        out["total_event_order_eligible_events"] = len(event_order_eligible)

        warnings = list(out.get("warnings", []))
        lines = [
            line
            for line in out.get("explanation_lines", [])
            if line != "No durable transition events available for pressure capture quality summary."
        ]

        if missing_or_unusable_event_order_count > 0:
            warnings.append("EVENT_ORDER_INELIGIBLE_EVENTS_SKIPPED")
            lines.append("Transition records without usable numeric event_order were excluded from event-order selection.")

        if reason == "NO_EVENT_ORDER_ELIGIBLE_EVENTS":
            out["summary_available"] = False
            lines.append("No transition events with usable event_order are available for event-order windowed summary.")
        elif reason == "EMPTY_EVENT_ORDER_WINDOW_SELECTION":
            warnings.append("EMPTY_EVENT_ORDER_WINDOW_SELECTION")
            lines.append("Event-order window selection contains zero eligible transition events.")

        out["warnings"] = sorted(set(warnings))
        if lines:
            out["explanation_lines"] = lines
        return out

    def get_pressure_capture_quality_window_comparator(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        index_max_events: Optional[int] = None,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        event_order_max_events: Optional[int] = None,
    ) -> dict:
        """
        Read-only comparator between index-window (v1.5) and event_order-window (v1.6)
        capture quality summaries.
        """
        index_summary = self.get_pressure_capture_quality_summary_window(
            start_index=start_index,
            end_index=end_index,
            max_events=index_max_events,
        )
        event_order_summary = self.get_pressure_capture_quality_summary_event_order_window(
            start_event_order=start_event_order,
            end_event_order=end_event_order,
            max_events=event_order_max_events,
        )

        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        def _delta(a: int, b: int) -> int:
            # Explicit comparator direction: event_order minus index.
            return _as_int(b) - _as_int(a)

        def _delta_counts(
            index_counts: Optional[dict],
            order_counts: Optional[dict],
            known_keys: Optional[list[str]] = None,
        ) -> dict:
            a = index_counts if isinstance(index_counts, dict) else {}
            b = order_counts if isinstance(order_counts, dict) else {}
            keys = set(a.keys()) | set(b.keys())
            if known_keys:
                keys |= set(known_keys)
            return {k: _delta(a.get(k, 0), b.get(k, 0)) for k in sorted(keys)}

        index_available = bool(index_summary.get("summary_available", False))
        event_order_available = bool(event_order_summary.get("summary_available", False))

        comparison = {
            "index_window_available": index_available,
            "event_order_window_available": event_order_available,
            "total_transition_events_delta": _delta(
                index_summary.get("total_transition_events", 0),
                event_order_summary.get("total_transition_events", 0),
            ),
            "window_event_count_delta": _delta(
                index_summary.get("window_event_count", 0),
                event_order_summary.get("window_event_count", 0),
            ),
            "auditable_event_count_delta": _delta(
                index_summary.get("auditable_event_count", 0),
                event_order_summary.get("auditable_event_count", 0),
            ),
            "pressure_snapshot_present_count_delta": _delta(
                index_summary.get("pressure_snapshot_present_count", 0),
                event_order_summary.get("pressure_snapshot_present_count", 0),
            ),
            "pressure_snapshot_missing_count_delta": _delta(
                index_summary.get("pressure_snapshot_missing_count", 0),
                event_order_summary.get("pressure_snapshot_missing_count", 0),
            ),
            "audit_state_count_deltas": _delta_counts(
                index_summary.get("audit_state_counts", {}),
                event_order_summary.get("audit_state_counts", {}),
                known_keys=[
                    "PRESSURE_CAPTURE_AUDIT_VALID",
                    "PRESSURE_CAPTURE_AUDIT_INVALID",
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE",
                ],
            ),
            "capture_reason_count_deltas": _delta_counts(
                index_summary.get("capture_reason_counts", {}),
                event_order_summary.get("capture_reason_counts", {}),
                known_keys=[
                    "PRESSURE_CAPTURE_FULL",
                    "PRESSURE_CAPTURE_PARTIAL",
                    "PRESSURE_CAPTURE_FAILED",
                    "UNRECOGNIZED_CAPTURE_REASON",
                ],
            ),
            "recoverability_count_deltas": _delta_counts(
                index_summary.get("recoverability_counts", {}),
                event_order_summary.get("recoverability_counts", {}),
                known_keys=[
                    "FULLY_RECOVERABLE",
                    "PARTIALLY_RECOVERABLE",
                    "UNRECOVERABLE",
                ],
            ),
            "event_type_count_deltas": _delta_counts(
                index_summary.get("event_type_counts", {}),
                event_order_summary.get("event_type_counts", {}),
            ),
        }

        mismatch_flags: list[str] = []
        if not index_available:
            mismatch_flags.append("INDEX_WINDOW_UNAVAILABLE")
        if not event_order_available:
            mismatch_flags.append("EVENT_ORDER_WINDOW_UNAVAILABLE")

        if index_available and event_order_available:
            if comparison["window_event_count_delta"] != 0:
                mismatch_flags.append("WINDOW_COUNT_MISMATCH")
            if any(v != 0 for v in comparison["audit_state_count_deltas"].values()):
                mismatch_flags.append("AUDIT_STATE_MISMATCH")
            if any(v != 0 for v in comparison["capture_reason_count_deltas"].values()):
                mismatch_flags.append("CAPTURE_REASON_MISMATCH")
            if any(v != 0 for v in comparison["recoverability_count_deltas"].values()):
                mismatch_flags.append("RECOVERABILITY_MISMATCH")
            if any(v != 0 for v in comparison["event_type_count_deltas"].values()):
                mismatch_flags.append("EVENT_TYPE_MISMATCH")
            if not mismatch_flags:
                mismatch_flags.append("NO_MISMATCH_DETECTED")

        if not index_available and not event_order_available:
            reason = "BOTH_WINDOWS_UNAVAILABLE"
        elif not index_available:
            reason = "INDEX_WINDOW_UNAVAILABLE"
        elif not event_order_available:
            reason = "EVENT_ORDER_WINDOW_UNAVAILABLE"
        elif "NO_MISMATCH_DETECTED" in mismatch_flags:
            reason = "WINDOW_SUMMARIES_MATCH"
        else:
            reason = "WINDOW_SUMMARIES_DIFFER"

        warnings = sorted(
            set(
                list(index_summary.get("warnings", []))
                + list(event_order_summary.get("warnings", []))
            )
        )

        explanation_lines: list[str] = [
            "Comparator deltas use event_order_window minus index_window counts."
        ]
        if not index_available and not event_order_available:
            explanation_lines.append("Both window summaries are unavailable under requested bounds.")
        elif not index_available or not event_order_available:
            explanation_lines.append("Window availability mismatch detected between index and event_order summaries.")
        else:
            if "NO_MISMATCH_DETECTED" in mismatch_flags:
                explanation_lines.append("No count mismatches detected between index-window and event_order-window summaries.")
            else:
                explanation_lines.append("Count mismatches detected between index-window and event_order-window summaries.")
                if "WINDOW_COUNT_MISMATCH" in mismatch_flags:
                    explanation_lines.append("Selection mismatch detected: window_event_count differs between methods.")
                bucket_mismatch_flags = [
                    "AUDIT_STATE_MISMATCH",
                    "CAPTURE_REASON_MISMATCH",
                    "RECOVERABILITY_MISMATCH",
                    "EVENT_TYPE_MISMATCH",
                ]
                if any(f in mismatch_flags for f in bucket_mismatch_flags):
                    explanation_lines.append("Bucket-count mismatch detected for one or more preserved summary groups.")

        return {
            "comparison_available": bool(index_available or event_order_available),
            "comparison_mode": "LEDGER_READ_ONLY_WINDOW_COMPARATOR",
            "reason": reason,
            "request_spec": {
                "start_index": start_index,
                "end_index": end_index,
                "index_max_events": index_max_events,
                "start_event_order": start_event_order,
                "end_event_order": end_event_order,
                "event_order_max_events": event_order_max_events,
            },
            "index_window_summary": index_summary,
            "event_order_window_summary": event_order_summary,
            "comparison": comparison,
            "mismatch_flags": mismatch_flags,
            "warnings": warnings,
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_observability_stage_lock_audit(self) -> dict:
        """
        Read-only stage-lock audit for observability APIs (v1.4-v1.7).
        Verifies consistency contracts without mutating any lineage or ledger state.
        """
        expected_bucket_keys = {
            "audit_state_counts": {
                "PRESSURE_CAPTURE_AUDIT_VALID",
                "PRESSURE_CAPTURE_AUDIT_INVALID",
                "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE",
            },
            "capture_reason_counts": {
                "PRESSURE_CAPTURE_FULL",
                "PRESSURE_CAPTURE_PARTIAL",
                "PRESSURE_CAPTURE_FAILED",
                "UNRECOGNIZED_CAPTURE_REASON",
            },
            "recoverability_counts": {
                "FULLY_RECOVERABLE",
                "PARTIALLY_RECOVERABLE",
                "UNRECOVERABLE",
            },
        }

        required_surfaces = {
            "summary_api_present": callable(getattr(self, "get_pressure_capture_quality_summary", None)),
            "index_window_api_present": callable(getattr(self, "get_pressure_capture_quality_summary_window", None)),
            "event_order_window_api_present": callable(getattr(self, "get_pressure_capture_quality_summary_event_order_window", None)),
            "comparator_api_present": callable(getattr(self, "get_pressure_capture_quality_window_comparator", None)),
        }

        contract_surface = {
            **required_surfaces,
            "bucket_surfaces": {
                "expected_bucket_keys": {k: sorted(v) for k, v in expected_bucket_keys.items()},
                "observed_bucket_keys": {},
            },
            "window_semantics": {
                "index_window_start_index": "INCLUSIVE",
                "index_window_end_index": "EXCLUSIVE",
                "event_order_window_start_event_order": "INCLUSIVE",
                "event_order_window_end_event_order": "INCLUSIVE",
            },
            "comparator_delta_direction": "event_order_window - index_window",
        }

        if not all(required_surfaces.values()):
            missing = sorted([k for k, v in required_surfaces.items() if not v])
            return {
                "audit_available": False,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                "reason": "REQUIRED_SURFACE_MISSING",
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": contract_surface,
                "warnings": ["REQUIRED_SURFACE_MISSING"],
                "explanation_lines": [f"Required observability surface missing: {', '.join(missing)}."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        check_results: list[dict] = []
        warnings: list[str] = []
        explanation_lines: list[str] = []

        def _add_check(check_name: str, passed: bool, reason: str, details: dict) -> None:
            check_results.append(
                {
                    "check_name": check_name,
                    "passed": bool(passed),
                    "reason": reason,
                    "details": details,
                }
            )

        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        def _delta(a: int, b: int) -> int:
            return _as_int(b) - _as_int(a)

        def _delta_counts(a: Optional[dict], b: Optional[dict], expected: set[str]) -> dict:
            left = a if isinstance(a, dict) else {}
            right = b if isinstance(b, dict) else {}
            keys = set(left.keys()) | set(right.keys()) | set(expected)
            return {k: _delta(left.get(k, 0), right.get(k, 0)) for k in sorted(keys)}

        def _extract_bucket_keys(summary: dict) -> dict:
            keys: dict[str, list[str]] = {}
            for field in expected_bucket_keys.keys():
                raw = summary.get(field, {})
                keys[field] = sorted(raw.keys()) if isinstance(raw, dict) else []
            return keys

        try:
            s14 = self.get_pressure_capture_quality_summary()
            s15 = self.get_pressure_capture_quality_summary_window()
            s16 = self.get_pressure_capture_quality_summary_event_order_window()
            cmp_out = self.get_pressure_capture_quality_window_comparator()
        except Exception as exc:
            return {
                "audit_available": False,
                "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                "reason": "AUDIT_EXECUTION_EXCEPTION",
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": contract_surface,
                "warnings": ["AUDIT_EXECUTION_EXCEPTION"],
                "explanation_lines": [f"Observability stage-lock audit failed to execute: {type(exc).__name__}."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        contract_surface["bucket_surfaces"]["observed_bucket_keys"] = {
            "v1_4_summary": _extract_bucket_keys(s14),
            "v1_5_index_window": _extract_bucket_keys(s15),
            "v1_6_event_order_window": _extract_bucket_keys(s16),
            "v1_7_comparator_index_side": _extract_bucket_keys(cmp_out.get("index_window_summary", {})),
            "v1_7_comparator_event_order_side": _extract_bucket_keys(cmp_out.get("event_order_window_summary", {})),
        }

        # 1) Full-range index window should match v1.4 summary on the same ledger.
        fields_to_match = [
            "total_transition_events",
            "auditable_event_count",
            "pressure_snapshot_present_count",
            "pressure_snapshot_missing_count",
            "audit_state_counts",
            "capture_reason_counts",
            "recoverability_counts",
            "event_type_counts",
            "event_type_breakdown",
        ]
        mismatch_fields = [f for f in fields_to_match if s14.get(f) != s15.get(f)]
        _add_check(
            "FULL_RANGE_INDEX_EQUALS_V14",
            passed=(len(mismatch_fields) == 0),
            reason="MATCH" if len(mismatch_fields) == 0 else "FIELD_MISMATCH",
            details={"mismatch_fields": mismatch_fields},
        )

        # 2) Comparator index side should match direct v1.5 output.
        cmp_index = cmp_out.get("index_window_summary")
        _add_check(
            "COMPARATOR_INDEX_SIDE_MATCHES_V15",
            passed=(cmp_index == s15),
            reason="MATCH" if cmp_index == s15 else "MISMATCH",
            details={"index_side_present": isinstance(cmp_index, dict)},
        )

        # 3) Comparator event_order side should match direct v1.6 output.
        cmp_order = cmp_out.get("event_order_window_summary")
        _add_check(
            "COMPARATOR_EVENT_ORDER_SIDE_MATCHES_V16",
            passed=(cmp_order == s16),
            reason="MATCH" if cmp_order == s16 else "MISMATCH",
            details={"event_order_side_present": isinstance(cmp_order, dict)},
        )

        # 4) Bucket names/category sets should remain unchanged.
        bucket_surface_issues: list[str] = []
        for surface_name, surface_keys in contract_surface["bucket_surfaces"]["observed_bucket_keys"].items():
            for field, expected in expected_bucket_keys.items():
                got = set(surface_keys.get(field, []))
                if got != expected:
                    bucket_surface_issues.append(f"{surface_name}:{field}")
        _add_check(
            "BUCKET_SURFACE_STABILITY",
            passed=(len(bucket_surface_issues) == 0),
            reason="STABLE" if len(bucket_surface_issues) == 0 else "BUCKET_SURFACE_DRIFT",
            details={"issues": bucket_surface_issues},
        )

        # 5) Read-only guardrail flags should remain false.
        guardrail_keys = [
            "lineage_mutation_performed",
            "event_creation_performed",
            "history_rewrite_performed",
        ]
        guardrail_issues: list[str] = []
        for name, payload in [
            ("v1_4_summary", s14),
            ("v1_5_index_window", s15),
            ("v1_6_event_order_window", s16),
            ("v1_7_comparator", cmp_out),
        ]:
            for key in guardrail_keys:
                if payload.get(key) is not False:
                    guardrail_issues.append(f"{name}:{key}")
        _add_check(
            "READ_ONLY_GUARDRAILS_FALSE",
            passed=(len(guardrail_issues) == 0),
            reason="READ_ONLY_OK" if len(guardrail_issues) == 0 else "READ_ONLY_FLAG_VIOLATION",
            details={"issues": guardrail_issues},
        )

        # 6) Known unavailable cases should remain unavailable honestly.
        invalid_index = self.get_pressure_capture_quality_summary_window(start_index=1, end_index=0)
        invalid_order = self.get_pressure_capture_quality_summary_event_order_window(start_event_order=1, end_event_order=0)
        invalid_cmp = self.get_pressure_capture_quality_window_comparator(
            start_index=1,
            end_index=0,
            start_event_order=1,
            end_event_order=0,
        )
        unavailable_ok = (
            invalid_index.get("summary_available") is False
            and invalid_index.get("reason") == "INVALID_WINDOW_BOUNDS"
            and invalid_order.get("summary_available") is False
            and invalid_order.get("reason") == "INVALID_EVENT_ORDER_BOUNDS"
            and invalid_cmp.get("comparison_available") is False
            and invalid_cmp.get("reason") == "BOTH_WINDOWS_UNAVAILABLE"
        )
        _add_check(
            "UNAVAILABLE_CASES_REMAIN_UNAVAILABLE",
            passed=unavailable_ok,
            reason="UNAVAILABLE_BEHAVIOR_OK" if unavailable_ok else "UNAVAILABLE_BEHAVIOR_MISMATCH",
            details={
                "invalid_index_reason": invalid_index.get("reason"),
                "invalid_order_reason": invalid_order.get("reason"),
                "invalid_comparator_reason": invalid_cmp.get("reason"),
            },
        )

        # 7) Comparator delta direction and math must remain event_order - index.
        cmp_section = cmp_out.get("comparison", {})
        expected_deltas = {
            "total_transition_events_delta": _delta(
                s15.get("total_transition_events", 0),
                s16.get("total_transition_events", 0),
            ),
            "window_event_count_delta": _delta(
                s15.get("window_event_count", 0),
                s16.get("window_event_count", 0),
            ),
            "auditable_event_count_delta": _delta(
                s15.get("auditable_event_count", 0),
                s16.get("auditable_event_count", 0),
            ),
            "pressure_snapshot_present_count_delta": _delta(
                s15.get("pressure_snapshot_present_count", 0),
                s16.get("pressure_snapshot_present_count", 0),
            ),
            "pressure_snapshot_missing_count_delta": _delta(
                s15.get("pressure_snapshot_missing_count", 0),
                s16.get("pressure_snapshot_missing_count", 0),
            ),
            "audit_state_count_deltas": _delta_counts(
                s15.get("audit_state_counts", {}),
                s16.get("audit_state_counts", {}),
                expected_bucket_keys["audit_state_counts"],
            ),
            "capture_reason_count_deltas": _delta_counts(
                s15.get("capture_reason_counts", {}),
                s16.get("capture_reason_counts", {}),
                expected_bucket_keys["capture_reason_counts"],
            ),
            "recoverability_count_deltas": _delta_counts(
                s15.get("recoverability_counts", {}),
                s16.get("recoverability_counts", {}),
                expected_bucket_keys["recoverability_counts"],
            ),
            "event_type_count_deltas": _delta_counts(
                s15.get("event_type_counts", {}),
                s16.get("event_type_counts", {}),
                set(),
            ),
        }
        delta_mismatches: list[str] = []
        for k, v in expected_deltas.items():
            if cmp_section.get(k) != v:
                delta_mismatches.append(k)
        _add_check(
            "COMPARATOR_DELTA_DIRECTION_AND_MATH",
            passed=(len(delta_mismatches) == 0),
            reason="DELTA_DIRECTION_OK" if len(delta_mismatches) == 0 else "DELTA_DIRECTION_OR_MATH_MISMATCH",
            details={"mismatch_fields": delta_mismatches},
        )

        checks_run = len(check_results)
        checks_passed = len([c for c in check_results if c.get("passed") is True])
        checks_failed = checks_run - checks_passed

        if checks_failed == 0:
            lock_state = "OBSERVABILITY_STAGE_LOCKED"
            reason = "ALL_REQUIRED_CHECKS_PASSED"
            explanation_lines.append("Observability stage-lock checks passed across v1.4-v1.7 surfaces.")
        else:
            lock_state = "OBSERVABILITY_STAGE_LOCK_INCONSISTENT"
            reason = "CHECK_FAILURES_DETECTED"
            warnings.append("OBSERVABILITY_STAGE_LOCK_CHECK_FAILURES")
            explanation_lines.append("One or more observability stage-lock checks failed; surfaces are inconsistent.")

        return {
            "audit_available": True,
            "audit_mode": "OBSERVABILITY_STAGE_LOCK",
            "lock_state": lock_state,
            "reason": reason,
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "check_results": check_results,
            "contract_surface": contract_surface,
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_stage_lock_audit(self) -> dict:
        _GUARDRAIL_FIELDS = [
            "lineage_mutation_performed",
            "event_creation_performed",
            "history_rewrite_performed",
        ]
        _OBS_API = "get_observability_stage_lock_audit"
        _CB_API = "get_cross_band_stage_lock_audit"

        def _check_pass(name, reason, details=None):
            return {
                "check_name": name,
                "passed": True,
                "reason": reason,
                "details": details if details is not None else {},
            }

        def _check_fail(name, reason, details=None):
            return {
                "check_name": name,
                "passed": False,
                "reason": reason,
                "details": details if details is not None else {},
            }

        def _unavailable(reason, explanation, obs_result, cb_result):
            return {
                "audit_available": False,
                "audit_mode": "SYSTEM_STAGE_LOCK",
                "lock_state": "SYSTEM_STAGE_LOCK_UNAVAILABLE",
                "reason": reason,
                "sub_audits": {
                    "observability_stage_lock": obs_result,
                    "cross_band_stage_lock": cb_result,
                },
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "warnings": [],
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        obs_callable = callable(getattr(self, _OBS_API, None))
        cb_callable = callable(getattr(self, _CB_API, None))
        if not obs_callable or not cb_callable:
            missing_apis = []
            if not obs_callable:
                missing_apis.append(_OBS_API)
            if not cb_callable:
                missing_apis.append(_CB_API)
            return _unavailable(
                "REQUIRED_SUB_AUDIT_API_MISSING",
                "Missing required sub-audit APIs: " + ", ".join(missing_apis),
                None,
                None,
            )

        obs_result = None
        cb_result = None
        try:
            obs_result = self.get_observability_stage_lock_audit()
        except Exception as exc:
            return _unavailable(
                "SUB_AUDIT_CALL_FAILED",
                "get_observability_stage_lock_audit() raised: " + str(exc),
                None,
                None,
            )
        try:
            cb_result = self.get_cross_band_stage_lock_audit()
        except Exception as exc:
            return _unavailable(
                "SUB_AUDIT_CALL_FAILED",
                "get_cross_band_stage_lock_audit() raised: " + str(exc),
                obs_result,
                None,
            )

        check_results = []
        warnings = []

        obs_mode_ok = (
            isinstance(obs_result, dict)
            and obs_result.get("audit_mode") == "OBSERVABILITY_STAGE_LOCK"
            and "lock_state" in obs_result
        )
        if obs_mode_ok:
            check_results.append(_check_pass(
                "OBSERVABILITY_STAGE_LOCK_PRESENT_AND_USABLE",
                "audit_mode and lock_state present in observability sub-audit",
                {"audit_mode": obs_result.get("audit_mode"), "lock_state": obs_result.get("lock_state")},
            ))
        else:
            check_results.append(_check_fail(
                "OBSERVABILITY_STAGE_LOCK_PRESENT_AND_USABLE",
                "observability sub-audit missing expected audit_mode or lock_state",
                {"obs_result_type": type(obs_result).__name__},
            ))

        cb_mode_ok = (
            isinstance(cb_result, dict)
            and cb_result.get("audit_mode") == "CROSS_BAND_STAGE_LOCK"
            and "lock_state" in cb_result
        )
        if cb_mode_ok:
            check_results.append(_check_pass(
                "CROSS_BAND_STAGE_LOCK_PRESENT_AND_USABLE",
                "audit_mode and lock_state present in cross-band sub-audit",
                {"audit_mode": cb_result.get("audit_mode"), "lock_state": cb_result.get("lock_state")},
            ))
        else:
            check_results.append(_check_fail(
                "CROSS_BAND_STAGE_LOCK_PRESENT_AND_USABLE",
                "cross-band sub-audit missing expected audit_mode or lock_state",
                {"cb_result_type": type(cb_result).__name__},
            ))

        if not obs_mode_ok or not cb_mode_ok:
            failed_shape = [c["check_name"] for c in check_results if not c["passed"]]
            return {
                "audit_available": False,
                "audit_mode": "SYSTEM_STAGE_LOCK",
                "lock_state": "SYSTEM_STAGE_LOCK_UNAVAILABLE",
                "reason": "SUB_AUDIT_SHAPE_INVALID",
                "sub_audits": {
                    "observability_stage_lock": obs_result,
                    "cross_band_stage_lock": cb_result,
                },
                "checks_run": len(check_results),
                "checks_passed": sum(1 for c in check_results if c["passed"]),
                "checks_failed": sum(1 for c in check_results if not c["passed"]),
                "check_results": check_results,
                "warnings": warnings,
                "explanation_lines": [
                    "Sub-audit shape invalid; failed: " + ", ".join(failed_shape)
                ],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        obs_lock = obs_result["lock_state"]
        cb_lock = cb_result["lock_state"]

        obs_lock_ok = obs_lock in ("OBSERVABILITY_STAGE_LOCKED", "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE")
        if obs_lock_ok:
            check_results.append(_check_pass(
                "OBSERVABILITY_STAGE_LOCKED_WHEN_AVAILABLE",
                "observability band is locked or honestly unavailable",
                {"lock_state": obs_lock},
            ))
        else:
            check_results.append(_check_fail(
                "OBSERVABILITY_STAGE_LOCKED_WHEN_AVAILABLE",
                "observability band reports INCONSISTENT",
                {"lock_state": obs_lock},
            ))
            warnings.append("OBSERVABILITY_INCONSISTENT: " + obs_lock)

        cb_lock_ok = cb_lock in ("CROSS_BAND_STAGE_LOCKED", "CROSS_BAND_STAGE_LOCK_UNAVAILABLE")
        if cb_lock_ok:
            check_results.append(_check_pass(
                "CROSS_BAND_STAGE_LOCKED_WHEN_AVAILABLE",
                "cross-band band is locked or honestly unavailable",
                {"lock_state": cb_lock},
            ))
        else:
            check_results.append(_check_fail(
                "CROSS_BAND_STAGE_LOCKED_WHEN_AVAILABLE",
                "cross-band band reports INCONSISTENT",
                {"lock_state": cb_lock},
            ))
            warnings.append("CROSS_BAND_INCONSISTENT: " + cb_lock)

        guardrail_violations = []
        for field in _GUARDRAIL_FIELDS:
            if obs_result.get(field) is not False:
                guardrail_violations.append("observability." + field)
            if cb_result.get(field) is not False:
                guardrail_violations.append("cross_band." + field)
        if not guardrail_violations:
            check_results.append(_check_pass(
                "READ_ONLY_GUARDRAILS_FALSE",
                "all read-only guardrails are False in both sub-audits",
                {"checked_fields": _GUARDRAIL_FIELDS},
            ))
        else:
            check_results.append(_check_fail(
                "READ_ONLY_GUARDRAILS_FALSE",
                "guardrail violation in sub-audit(s): " + ", ".join(guardrail_violations),
                {"violations": guardrail_violations},
            ))
            warnings.append("GUARDRAIL_VIOLATION: " + ", ".join(guardrail_violations))

        checks_run = len(check_results)
        checks_passed = sum(1 for c in check_results if c["passed"])
        checks_failed = checks_run - checks_passed

        explanation_lines = []
        if checks_failed == 0:
            if (
                obs_lock == "OBSERVABILITY_STAGE_LOCKED"
                and cb_lock == "CROSS_BAND_STAGE_LOCKED"
            ):
                lock_state = "SYSTEM_STAGE_LOCKED"
                reason = "ALL_SUB_AUDITS_LOCKED"
                explanation_lines.append("All 5 checks passed. Both bands stage-locked.")
            else:
                lock_state = "SYSTEM_STAGE_LOCK_UNAVAILABLE"
                reason = "SUB_AUDIT_NOT_LOCKED"
                unavailable_bands = []
                if obs_lock != "OBSERVABILITY_STAGE_LOCKED":
                    unavailable_bands.append("observability(" + obs_lock + ")")
                if cb_lock != "CROSS_BAND_STAGE_LOCKED":
                    unavailable_bands.append("cross_band(" + cb_lock + ")")
                explanation_lines.append(
                    "Checks passed but band(s) not fully locked: " + ", ".join(unavailable_bands)
                )
        else:
            lock_state = "SYSTEM_STAGE_LOCK_INCONSISTENT"
            reason = "CONSISTENCY_CHECK_FAILED"
            failed_names = [c["check_name"] for c in check_results if not c["passed"]]
            explanation_lines.append("Failed checks: " + ", ".join(failed_names))

        return {
            "audit_available": True,
            "audit_mode": "SYSTEM_STAGE_LOCK",
            "lock_state": lock_state,
            "reason": reason,
            "sub_audits": {
                "observability_stage_lock": obs_result,
                "cross_band_stage_lock": cb_result,
            },
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "check_results": check_results,
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_lock_gate_posture(self) -> dict:
        """
        Implementation of System Lock Consumer Gate v1.1.
        Consumes get_system_stage_lock_audit() exactly once to provide a top-level gate posture.

        This is a strictly read-only posture layer.
        - No semantics, mutation, repair, or recommendations.
        - Preserves lineage honestly.
        - Single-call discipline enforced.
        """
        # Call get_system_stage_lock_audit() exactly once
        audit = self.get_system_stage_lock_audit()

        # Extract base status from umbrella audit
        audit_available = audit.get("audit_available", False)
        lock_state = audit.get("lock_state", "SYSTEM_STAGE_LOCK_UNAVAILABLE")
        audit_reason = audit.get("reason", "AUDIT_REASON_MISSING")

        # Map umbrella lock_state to gate_state and gate_reason
        # SYSTEM_STAGE_LOCKED -> SYSTEM_GATE_LOCKED
        # SYSTEM_STAGE_LOCK_INCONSISTENT -> SYSTEM_GATE_INCONSISTENT
        # SYSTEM_STAGE_LOCK_UNAVAILABLE -> SYSTEM_GATE_UNAVAILABLE
        # Otherwise -> SYSTEM_GATE_UNAVAILABLE (favoring non-overclaiming)

        if not audit_available:
            gate_state = "SYSTEM_GATE_UNAVAILABLE"
            gate_reason = "SYSTEM_STAGE_LOCK_AUDIT_UNAVAILABLE"
        elif lock_state == "SYSTEM_STAGE_LOCKED":
            gate_state = "SYSTEM_GATE_LOCKED"
            gate_reason = "SYSTEM_STAGE_LOCKED"
        elif lock_state == "SYSTEM_STAGE_LOCK_INCONSISTENT":
            gate_state = "SYSTEM_GATE_INCONSISTENT"
            gate_reason = "SYSTEM_STAGE_LOCK_INCONSISTENT"
        elif lock_state == "SYSTEM_STAGE_LOCK_UNAVAILABLE":
            gate_state = "SYSTEM_GATE_UNAVAILABLE"
            gate_reason = "SYSTEM_STAGE_LOCK_UNAVAILABLE"
        else:
            # Fallback for unexpected states: favor unavailable over false locked
            gate_state = "SYSTEM_GATE_UNAVAILABLE"
            gate_reason = "SYSTEM_STAGE_LOCK_AUDIT_UNUSABLE"

        # Construct explanation lines based on audit result
        explanation_lines = [
            f"Gate posture: {gate_state}",
            f"Gate reason: {gate_reason}",
            f"Umbrella lock state: {lock_state}",
        ]
        if audit.get("explanation_lines"):
            explanation_lines.extend(audit["explanation_lines"])

        # Construct final posture output
        return {
            "gate_available": True,
            "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
            "gate_state": gate_state,
            "gate_reason": gate_reason,
            "system_stage_lock": audit,
            "warnings": audit.get("warnings", []),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_cross_band_evidence_review_summary(self) -> dict:
        """
        Implementation of Cross-Band Evidence Review Summary v1.0.
        Read-only review layer over already-locked cross-band surfaces.
        Composes from existing cross-band APIs without reinterpretation or decision logic.
        """
        # Gather underlying cross-band evidence (full range)
        window_summary = self.get_cross_band_self_check_summary_window()
        stage_lock_audit = self.get_cross_band_stage_lock_audit()

        # Compositional logic for review_state and review_reason
        lock_state = stage_lock_audit.get("lock_state", "CROSS_BAND_STAGE_LOCK_UNAVAILABLE")
        summary_available = window_summary.get("summary_available", False)
        auditable_event_count = window_summary.get("auditable_event_count", 0)

        # READY only when cross-band stage lock is LOCKED and sufficient surface exists
        if lock_state == "CROSS_BAND_STAGE_LOCKED" and summary_available and auditable_event_count > 0:
            review_state = "CROSS_BAND_EVIDENCE_REVIEW_READY"
            review_reason = "CROSS_BAND_STAGE_LOCKED_WITH_RELEVANT_SURFACE"
        # PARTIAL when evidence exists but coverage is limited or mixed
        elif summary_available and auditable_event_count > 0:
            review_state = "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL"
            review_reason = "LIMITED_OR_MIXED_EVIDENCE_SURFACE"
        # PARTIAL if stage lock is inconsistent even if auditable count is 0
        elif summary_available and lock_state == "CROSS_BAND_STAGE_LOCK_INCONSISTENT" and auditable_event_count > 0:
            review_state = "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL"
            review_reason = "INCONSISTENT_STAGE_LOCK_POSTURE"
        # UNAVAILABLE when required surfaces are missing or no auditable evidence exists
        else:
            review_state = "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"
            review_reason = "EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING"

        # Gather counts and scope details
        evidence_counts = window_summary.get("self_check_state_counts", {
            "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
            "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
            "CROSS_BAND_PARTIAL": 0,
            "CROSS_BAND_UNAVAILABLE": 0,
        })
        contradiction_flag_counts = window_summary.get("contradiction_flag_counts", {})
        event_type_counts = window_summary.get("event_type_counts", {})

        evidence_scope = {
            "total_transition_events": window_summary.get("total_transition_events", 0),
            "total_auditable_events": auditable_event_count,
            "self_check_state_counts": evidence_counts,
            "event_order_eligible_events": window_summary.get("window_event_count", 0),
            "comparator_available": stage_lock_audit.get("contract_surface", {}).get("comparator_api_present", False),
            "stage_lock_state": lock_state,
            "coverage_notes": window_summary.get("explanation_lines", []),
        }

        # Supporting surfaces for honesty and lineage
        supporting_surfaces = {
            "cross_band_self_check_summary": window_summary,
            "cross_band_stage_lock_audit": stage_lock_audit,
        }

        # Explanation lines for transparency
        explanation_lines = [
            f"Review state: {review_state}",
            f"Review reason: {review_reason}",
            f"Cross-band stage lock: {lock_state}",
            f"Auditable events: {auditable_event_count}",
        ]
        if auditable_event_count == 0:
            explanation_lines.append("Note: Evidence surface is thin (0 auditable events).")

        return {
            "review_available": True,
            "review_mode": "CROSS_BAND_EVIDENCE_REVIEW",
            "review_state": review_state,
            "review_reason": review_reason,
            "evidence_scope": evidence_scope,
            "evidence_counts": evidence_counts,
            "contradiction_flag_counts": contradiction_flag_counts,
            "event_type_counts": event_type_counts,
            "supporting_surfaces": supporting_surfaces,
            "warnings": sorted(set(window_summary.get("warnings", []) + stage_lock_audit.get("warnings", []))),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def _build_cross_band_bounded_evidence_review(
        self,
        *,
        bounded_summary,
        comparator_summary,
        review_mode: str,
        scope_label: str,
    ) -> dict:
        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        state_counts = (
            bounded_summary.get("self_check_state_counts", {})
            if isinstance(bounded_summary.get("self_check_state_counts"), dict)
            else {
                "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                "CROSS_BAND_PARTIAL": 0,
                "CROSS_BAND_UNAVAILABLE": 0,
            }
        )
        contradiction_counts = (
            bounded_summary.get("contradiction_flag_counts", {})
            if isinstance(bounded_summary.get("contradiction_flag_counts"), dict)
            else {}
        )
        event_type_counts = (
            bounded_summary.get("event_type_counts", {})
            if isinstance(bounded_summary.get("event_type_counts"), dict)
            else {}
        )

        summary_available = bool(bounded_summary.get("summary_available", False))
        auditable_event_count = _as_int(bounded_summary.get("auditable_event_count", 0))
        alignment_count = _as_int(state_counts.get("CROSS_BAND_ALIGNMENT_OBSERVED", 0))
        contradiction_count = _as_int(state_counts.get("CROSS_BAND_CONTRADICTION_OBSERVED", 0))
        partial_count = _as_int(state_counts.get("CROSS_BAND_PARTIAL", 0))
        unavailable_count = _as_int(state_counts.get("CROSS_BAND_UNAVAILABLE", 0))

        ready = (
            summary_available
            and auditable_event_count > 0
            and alignment_count == auditable_event_count
            and contradiction_count == 0
            and partial_count == 0
            and unavailable_count == 0
        )
        meaningful_surface_exists = summary_available and auditable_event_count > 0

        if ready:
            review_state = "CROSS_BAND_EVIDENCE_REVIEW_READY"
            review_reason = "BOUNDED_ALIGNMENT_OBSERVED_WITH_AUDITABLE_SURFACE"
        elif meaningful_surface_exists:
            review_state = "CROSS_BAND_EVIDENCE_REVIEW_PARTIAL"
            review_reason = "BOUNDED_MIXED_OR_LIMITED_EVIDENCE_SURFACE"
        else:
            review_state = "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"
            review_reason = "BOUNDED_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING"

        warnings = []
        warnings.extend(bounded_summary.get("warnings", []))
        if isinstance(comparator_summary, dict):
            warnings.extend(comparator_summary.get("warnings", []))
            mismatch_flags = comparator_summary.get("mismatch_flags", [])
            if isinstance(mismatch_flags, list):
                mismatch_set = set(mismatch_flags)
                mismatch_set.discard("NO_MISMATCH_DETECTED")
                if mismatch_set:
                    warnings.append("COMPARATOR_CONTEXT_MISMATCH_FLAGS_PRESENT")
        else:
            warnings.append("CROSS_BAND_WINDOW_COMPARATOR_SURFACE_MISSING")

        comparator_reason = (
            comparator_summary.get("reason")
            if isinstance(comparator_summary, dict)
            else "COMPARATOR_CONTEXT_UNAVAILABLE"
        )

        explanation_lines = [
            f"Review state: {review_state}",
            f"Review reason: {review_reason}",
            f"Bounded scope: {scope_label}",
            f"Auditable events: {auditable_event_count}",
            "Bounded review posture is scope-limited and not equivalent to full-range cross-band review.",
            f"Comparator context reason (non-predicate): {comparator_reason}",
        ]
        if auditable_event_count == 0:
            explanation_lines.append("Bounded evidence surface is thin (0 auditable events).")

        return {
            "review_available": True,
            "review_mode": review_mode,
            "review_state": review_state,
            "review_reason": review_reason,
            "window_spec": (
                bounded_summary.get("window_spec", {})
                if isinstance(bounded_summary.get("window_spec"), dict)
                else {}
            ),
            "evidence_scope": {
                "bounded_scope": scope_label,
                "bounded_summary_mode": bounded_summary.get("summary_mode"),
                "bounded_summary_reason": bounded_summary.get("reason"),
                "total_transition_events": _as_int(bounded_summary.get("total_transition_events", 0)),
                "window_event_count": _as_int(bounded_summary.get("window_event_count", 0)),
                "total_auditable_events": auditable_event_count,
                "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                "coverage_notes": list(bounded_summary.get("explanation_lines", [])),
            },
            "evidence_counts": {
                "self_check_state_counts": state_counts,
                "contradiction_flag_counts": contradiction_counts,
                "event_type_counts": event_type_counts,
                "total_transition_events": _as_int(bounded_summary.get("total_transition_events", 0)),
                "window_event_count": _as_int(bounded_summary.get("window_event_count", 0)),
                "total_auditable_events": auditable_event_count,
            },
            "supporting_surfaces": {
                "bounded_cross_band_self_check_summary": bounded_summary,
                "cross_band_window_comparator_context": comparator_summary,
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_cross_band_evidence_review_summary_window(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Cross-Band Evidence Review Summary Windowed v1.1.
        Read-only bounded review mapping over index-window cross-band self-check summary.
        """
        summary_api_name = "get_cross_band_self_check_summary_window"
        comparator_api_name = "get_cross_band_self_check_window_comparator"

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            bounded_summary,
            comparator_summary,
            warnings: list[str],
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "CROSS_BAND_EVIDENCE_REVIEW_WINDOW",
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": reason,
                "window_spec": {},
                "evidence_scope": {
                    "bounded_scope": "INDEX_WINDOW",
                    "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "self_check_state_counts": {
                        "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                        "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                        "CROSS_BAND_PARTIAL": 0,
                        "CROSS_BAND_UNAVAILABLE": 0,
                    },
                    "contradiction_flag_counts": {},
                    "event_type_counts": {},
                    "total_transition_events": 0,
                    "window_event_count": 0,
                    "total_auditable_events": 0,
                },
                "supporting_surfaces": {
                    "bounded_cross_band_self_check_summary": bounded_summary,
                    "cross_band_window_comparator_context": comparator_summary,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if not callable(getattr(self, summary_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation="Required bounded cross-band source surface missing: get_cross_band_self_check_summary_window.",
                bounded_summary=None,
                comparator_summary=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        comparator_summary = None
        if callable(getattr(self, comparator_api_name, None)):
            try:
                comparator_summary = self.get_cross_band_self_check_window_comparator(
                    start_index=start_index,
                    end_index=end_index,
                    index_max_events=max_events,
                )
            except Exception:
                comparator_summary = None

        try:
            bounded_summary = self.get_cross_band_self_check_summary_window(
                start_index=start_index,
                end_index=end_index,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_cross_band_self_check_summary_window() raised {type(exc).__name__}.",
                bounded_summary=None,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "CROSS_BAND_WINDOW_SUMMARY_CALL_FAILED"],
            )

        shape_ok = (
            isinstance(bounded_summary, dict)
            and bounded_summary.get("summary_mode") == "CROSS_BAND_SELF_CHECK_WINDOW"
            and isinstance(bounded_summary.get("window_spec"), dict)
            and isinstance(bounded_summary.get("self_check_state_counts"), dict)
        )
        if not shape_ok:
            return _unavailable(
                reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Bounded cross-band window summary shape is invalid for evidence-review mapping.",
                bounded_summary=bounded_summary,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_SHAPE_INVALID"],
            )

        return self._build_cross_band_bounded_evidence_review(
            bounded_summary=bounded_summary,
            comparator_summary=comparator_summary,
            review_mode="CROSS_BAND_EVIDENCE_REVIEW_WINDOW",
            scope_label="INDEX_WINDOW",
        )

    def get_cross_band_evidence_review_summary_event_order_window(
        self,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Cross-Band Evidence Review Summary Event-Order Windowed v1.1.
        Read-only bounded review mapping over event-order-window cross-band self-check summary.
        """
        summary_api_name = "get_cross_band_self_check_summary_event_order_window"
        comparator_api_name = "get_cross_band_self_check_window_comparator"

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            bounded_summary,
            comparator_summary,
            warnings: list[str],
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "CROSS_BAND_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
                "review_state": "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": reason,
                "window_spec": {},
                "evidence_scope": {
                    "bounded_scope": "EVENT_ORDER_WINDOW",
                    "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "self_check_state_counts": {
                        "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                        "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                        "CROSS_BAND_PARTIAL": 0,
                        "CROSS_BAND_UNAVAILABLE": 0,
                    },
                    "contradiction_flag_counts": {},
                    "event_type_counts": {},
                    "total_transition_events": 0,
                    "window_event_count": 0,
                    "total_auditable_events": 0,
                },
                "supporting_surfaces": {
                    "bounded_cross_band_self_check_summary": bounded_summary,
                    "cross_band_window_comparator_context": comparator_summary,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if not callable(getattr(self, summary_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required bounded cross-band source surface missing: "
                    "get_cross_band_self_check_summary_event_order_window."
                ),
                bounded_summary=None,
                comparator_summary=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        comparator_summary = None
        if callable(getattr(self, comparator_api_name, None)):
            try:
                comparator_summary = self.get_cross_band_self_check_window_comparator(
                    start_event_order=start_event_order,
                    end_event_order=end_event_order,
                    event_order_max_events=max_events,
                )
            except Exception:
                comparator_summary = None

        try:
            bounded_summary = self.get_cross_band_self_check_summary_event_order_window(
                start_event_order=start_event_order,
                end_event_order=end_event_order,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_cross_band_self_check_summary_event_order_window() raised {type(exc).__name__}.",
                bounded_summary=None,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "CROSS_BAND_EVENT_ORDER_WINDOW_SUMMARY_CALL_FAILED"],
            )

        shape_ok = (
            isinstance(bounded_summary, dict)
            and bounded_summary.get("summary_mode") == "CROSS_BAND_SELF_CHECK_EVENT_ORDER_WINDOW"
            and isinstance(bounded_summary.get("window_spec"), dict)
            and isinstance(bounded_summary.get("self_check_state_counts"), dict)
        )
        if not shape_ok:
            return _unavailable(
                reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Bounded cross-band event-order summary shape is invalid for evidence-review mapping.",
                bounded_summary=bounded_summary,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_SHAPE_INVALID"],
            )

        return self._build_cross_band_bounded_evidence_review(
            bounded_summary=bounded_summary,
            comparator_summary=comparator_summary,
            review_mode="CROSS_BAND_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            scope_label="EVENT_ORDER_WINDOW",
        )

    def _build_observability_bounded_evidence_review(
        self,
        *,
        bounded_summary,
        comparator_summary,
        review_mode: str,
        scope_label: str,
    ) -> dict:
        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        audit_state_counts = (
            bounded_summary.get("audit_state_counts", {})
            if isinstance(bounded_summary.get("audit_state_counts"), dict)
            else {
                "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
            }
        )
        capture_reason_counts = (
            bounded_summary.get("capture_reason_counts", {})
            if isinstance(bounded_summary.get("capture_reason_counts"), dict)
            else {
                "PRESSURE_CAPTURE_FULL": 0,
                "PRESSURE_CAPTURE_PARTIAL": 0,
                "PRESSURE_CAPTURE_FAILED": 0,
                "UNRECOGNIZED_CAPTURE_REASON": 0,
            }
        )
        recoverability_counts = (
            bounded_summary.get("recoverability_counts", {})
            if isinstance(bounded_summary.get("recoverability_counts"), dict)
            else {
                "FULLY_RECOVERABLE": 0,
                "PARTIALLY_RECOVERABLE": 0,
                "UNRECOVERABLE": 0,
            }
        )
        event_type_counts = (
            bounded_summary.get("event_type_counts", {})
            if isinstance(bounded_summary.get("event_type_counts"), dict)
            else {}
        )

        summary_available = bool(bounded_summary.get("summary_available", False))
        auditable_event_count = _as_int(bounded_summary.get("auditable_event_count", 0))
        snapshot_present_count = _as_int(bounded_summary.get("pressure_snapshot_present_count", 0))
        snapshot_missing_count = _as_int(bounded_summary.get("pressure_snapshot_missing_count", 0))
        valid_count = _as_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_VALID", 0))
        invalid_count = _as_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_INVALID", 0))
        unavailable_count = _as_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_UNAVAILABLE", 0))

        ready = (
            summary_available
            and auditable_event_count > 0
            and valid_count == auditable_event_count
            and invalid_count == 0
            and unavailable_count == 0
        )
        meaningful_surface_exists = summary_available and auditable_event_count > 0

        if ready:
            review_state = "OBSERVABILITY_EVIDENCE_REVIEW_READY"
            review_reason = "BOUNDED_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE"
        elif meaningful_surface_exists:
            review_state = "OBSERVABILITY_EVIDENCE_REVIEW_PARTIAL"
            review_reason = "BOUNDED_LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE"
        else:
            review_state = "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
            review_reason = "BOUNDED_OBSERVABILITY_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING"

        warnings = []
        warnings.extend(bounded_summary.get("warnings", []))
        if isinstance(comparator_summary, dict):
            warnings.extend(comparator_summary.get("warnings", []))
            mismatch_flags = comparator_summary.get("mismatch_flags", [])
            if isinstance(mismatch_flags, list):
                mismatch_set = set(mismatch_flags)
                mismatch_set.discard("NO_MISMATCH_DETECTED")
                if mismatch_set:
                    warnings.append("COMPARATOR_CONTEXT_MISMATCH_FLAGS_PRESENT")
        else:
            warnings.append("OBSERVABILITY_WINDOW_COMPARATOR_SURFACE_MISSING")

        comparator_reason = (
            comparator_summary.get("reason")
            if isinstance(comparator_summary, dict)
            else "COMPARATOR_CONTEXT_UNAVAILABLE"
        )

        explanation_lines = [
            f"Review state: {review_state}",
            f"Review reason: {review_reason}",
            f"Bounded scope: {scope_label}",
            f"Auditable events: {auditable_event_count}",
            f"Audit valid/invalid/unavailable: {valid_count}/{invalid_count}/{unavailable_count}",
            "Bounded observability review posture is scope-limited and not equivalent to full-range observability review.",
            f"Comparator context reason (non-predicate): {comparator_reason}",
        ]
        if auditable_event_count == 0:
            explanation_lines.append("Bounded observability evidence surface is thin (0 auditable events).")

        return {
            "review_available": True,
            "review_mode": review_mode,
            "review_state": review_state,
            "review_reason": review_reason,
            "window_spec": (
                bounded_summary.get("window_spec", {})
                if isinstance(bounded_summary.get("window_spec"), dict)
                else {}
            ),
            "evidence_scope": {
                "bounded_scope": scope_label,
                "bounded_summary_mode": bounded_summary.get("summary_mode"),
                "bounded_summary_reason": bounded_summary.get("reason"),
                "total_transition_events": _as_int(bounded_summary.get("total_transition_events", 0)),
                "window_event_count": _as_int(bounded_summary.get("window_event_count", 0)),
                "total_auditable_events": auditable_event_count,
                "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                "coverage_notes": list(bounded_summary.get("explanation_lines", [])),
            },
            "evidence_counts": {
                "total_transition_events": _as_int(bounded_summary.get("total_transition_events", 0)),
                "window_event_count": _as_int(bounded_summary.get("window_event_count", 0)),
                "total_auditable_events": auditable_event_count,
                "pressure_snapshot_present_count": snapshot_present_count,
                "pressure_snapshot_missing_count": snapshot_missing_count,
                "audit_state_counts": audit_state_counts,
                "capture_reason_counts": capture_reason_counts,
                "recoverability_counts": recoverability_counts,
                "event_type_counts": event_type_counts,
            },
            "supporting_surfaces": {
                "bounded_observability_quality_summary": bounded_summary,
                "observability_window_comparator_context": comparator_summary,
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_observability_evidence_review_summary_window(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Observability Evidence Review Summary Windowed v1.1.
        Read-only bounded review mapping over index-window observability quality summary.
        """
        summary_api_name = "get_pressure_capture_quality_summary_window"
        comparator_api_name = "get_pressure_capture_quality_window_comparator"

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            bounded_summary,
            comparator_summary,
            warnings: list[str],
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW_WINDOW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": reason,
                "window_spec": {},
                "evidence_scope": {
                    "bounded_scope": "INDEX_WINDOW",
                    "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "total_transition_events": 0,
                    "window_event_count": 0,
                    "total_auditable_events": 0,
                    "pressure_snapshot_present_count": 0,
                    "pressure_snapshot_missing_count": 0,
                    "audit_state_counts": {
                        "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                    },
                    "capture_reason_counts": {
                        "PRESSURE_CAPTURE_FULL": 0,
                        "PRESSURE_CAPTURE_PARTIAL": 0,
                        "PRESSURE_CAPTURE_FAILED": 0,
                        "UNRECOGNIZED_CAPTURE_REASON": 0,
                    },
                    "recoverability_counts": {
                        "FULLY_RECOVERABLE": 0,
                        "PARTIALLY_RECOVERABLE": 0,
                        "UNRECOVERABLE": 0,
                    },
                    "event_type_counts": {},
                },
                "supporting_surfaces": {
                    "bounded_observability_quality_summary": bounded_summary,
                    "observability_window_comparator_context": comparator_summary,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if not callable(getattr(self, summary_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required bounded observability source surface missing: "
                    "get_pressure_capture_quality_summary_window."
                ),
                bounded_summary=None,
                comparator_summary=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        comparator_summary = None
        if callable(getattr(self, comparator_api_name, None)):
            try:
                comparator_summary = self.get_pressure_capture_quality_window_comparator(
                    start_index=start_index,
                    end_index=end_index,
                    index_max_events=max_events,
                )
            except Exception:
                comparator_summary = None

        try:
            bounded_summary = self.get_pressure_capture_quality_summary_window(
                start_index=start_index,
                end_index=end_index,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_pressure_capture_quality_summary_window() raised {type(exc).__name__}.",
                bounded_summary=None,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "OBSERVABILITY_WINDOW_SUMMARY_CALL_FAILED"],
            )

        shape_ok = (
            isinstance(bounded_summary, dict)
            and bounded_summary.get("summary_mode") == "LEDGER_READ_ONLY_WINDOWED"
            and isinstance(bounded_summary.get("window_spec"), dict)
            and isinstance(bounded_summary.get("audit_state_counts"), dict)
            and isinstance(bounded_summary.get("capture_reason_counts"), dict)
            and isinstance(bounded_summary.get("recoverability_counts"), dict)
        )
        if not shape_ok:
            return _unavailable(
                reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Bounded observability window summary shape is invalid for evidence-review mapping.",
                bounded_summary=bounded_summary,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_SHAPE_INVALID"],
            )

        return self._build_observability_bounded_evidence_review(
            bounded_summary=bounded_summary,
            comparator_summary=comparator_summary,
            review_mode="OBSERVABILITY_EVIDENCE_REVIEW_WINDOW",
            scope_label="INDEX_WINDOW",
        )

    def get_observability_evidence_review_summary_event_order_window(
        self,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Observability Evidence Review Summary Event-Order Windowed v1.1.
        Read-only bounded review mapping over event-order-window observability quality summary.
        """
        summary_api_name = "get_pressure_capture_quality_summary_event_order_window"
        comparator_api_name = "get_pressure_capture_quality_window_comparator"

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            bounded_summary,
            comparator_summary,
            warnings: list[str],
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": reason,
                "window_spec": {},
                "evidence_scope": {
                    "bounded_scope": "EVENT_ORDER_WINDOW",
                    "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "total_transition_events": 0,
                    "window_event_count": 0,
                    "total_auditable_events": 0,
                    "pressure_snapshot_present_count": 0,
                    "pressure_snapshot_missing_count": 0,
                    "audit_state_counts": {
                        "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                    },
                    "capture_reason_counts": {
                        "PRESSURE_CAPTURE_FULL": 0,
                        "PRESSURE_CAPTURE_PARTIAL": 0,
                        "PRESSURE_CAPTURE_FAILED": 0,
                        "UNRECOGNIZED_CAPTURE_REASON": 0,
                    },
                    "recoverability_counts": {
                        "FULLY_RECOVERABLE": 0,
                        "PARTIALLY_RECOVERABLE": 0,
                        "UNRECOVERABLE": 0,
                    },
                    "event_type_counts": {},
                },
                "supporting_surfaces": {
                    "bounded_observability_quality_summary": bounded_summary,
                    "observability_window_comparator_context": comparator_summary,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if not callable(getattr(self, summary_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required bounded observability source surface missing: "
                    "get_pressure_capture_quality_summary_event_order_window."
                ),
                bounded_summary=None,
                comparator_summary=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        comparator_summary = None
        if callable(getattr(self, comparator_api_name, None)):
            try:
                comparator_summary = self.get_pressure_capture_quality_window_comparator(
                    start_event_order=start_event_order,
                    end_event_order=end_event_order,
                    event_order_max_events=max_events,
                )
            except Exception:
                comparator_summary = None

        try:
            bounded_summary = self.get_pressure_capture_quality_summary_event_order_window(
                start_event_order=start_event_order,
                end_event_order=end_event_order,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=(
                    "get_pressure_capture_quality_summary_event_order_window() "
                    f"raised {type(exc).__name__}."
                ),
                bounded_summary=None,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "OBSERVABILITY_EVENT_ORDER_WINDOW_SUMMARY_CALL_FAILED"],
            )

        shape_ok = (
            isinstance(bounded_summary, dict)
            and bounded_summary.get("summary_mode") == "LEDGER_READ_ONLY_EVENT_ORDER_WINDOWED"
            and isinstance(bounded_summary.get("window_spec"), dict)
            and isinstance(bounded_summary.get("audit_state_counts"), dict)
            and isinstance(bounded_summary.get("capture_reason_counts"), dict)
            and isinstance(bounded_summary.get("recoverability_counts"), dict)
        )
        if not shape_ok:
            return _unavailable(
                reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Bounded observability event-order summary shape is invalid for evidence-review mapping.",
                bounded_summary=bounded_summary,
                comparator_summary=comparator_summary,
                warnings=["REQUIRED_SURFACE_SHAPE_INVALID"],
            )

        return self._build_observability_bounded_evidence_review(
            bounded_summary=bounded_summary,
            comparator_summary=comparator_summary,
            review_mode="OBSERVABILITY_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            scope_label="EVENT_ORDER_WINDOW",
        )

    def _build_system_bounded_evidence_review(
        self,
        *,
        cross_review,
        observability_review,
        review_mode: str,
        scope_label: str,
    ) -> dict:
        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        cross_scope = (
            cross_review.get("evidence_scope", {})
            if isinstance(cross_review.get("evidence_scope"), dict)
            else {}
        )
        obs_scope = (
            observability_review.get("evidence_scope", {})
            if isinstance(observability_review.get("evidence_scope"), dict)
            else {}
        )
        cross_counts = (
            cross_review.get("evidence_counts", {})
            if isinstance(cross_review.get("evidence_counts"), dict)
            else {}
        )
        obs_counts = (
            observability_review.get("evidence_counts", {})
            if isinstance(observability_review.get("evidence_counts"), dict)
            else {}
        )

        cross_auditable = _as_int(
            cross_scope.get(
                "total_auditable_events",
                cross_counts.get("total_auditable_events", 0),
            )
        )
        obs_auditable = _as_int(
            obs_scope.get(
                "total_auditable_events",
                obs_counts.get("total_auditable_events", 0),
            )
        )
        total_auditable = cross_auditable + obs_auditable

        cross_available = bool(cross_review.get("review_available", False))
        obs_available = bool(observability_review.get("review_available", False))
        cross_state = str(
            cross_review.get("review_state", "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE")
        )
        obs_state = str(
            observability_review.get(
                "review_state", "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
            )
        )
        cross_ready = cross_available and cross_state.endswith("_READY")
        obs_ready = obs_available and obs_state.endswith("_READY")

        ready = (
            cross_ready
            and obs_ready
            and cross_auditable > 0
            and obs_auditable > 0
        )
        meaningful_bounded_signal = total_auditable > 0

        if ready:
            review_state = "SYSTEM_EVIDENCE_REVIEW_READY"
            review_reason = "BOUNDED_COMPOSED_EVIDENCE_SURFACES_READY"
        elif not meaningful_bounded_signal:
            review_state = "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
            review_reason = "NO_MEANINGFUL_BOUNDED_EVIDENCE_SURFACE"
        else:
            review_state = "SYSTEM_EVIDENCE_REVIEW_PARTIAL"
            review_reason = "BOUNDED_LIMITED_OR_MIXED_EVIDENCE_SURFACE"

        warnings = []
        warnings.extend(cross_review.get("warnings", []))
        warnings.extend(observability_review.get("warnings", []))

        return {
            "review_available": True,
            "review_mode": review_mode,
            "review_state": review_state,
            "review_reason": review_reason,
            "window_spec": cross_review.get("window_spec", {}),
            "evidence_scope": {
                "bounded_scope": scope_label,
                "cross_band_review_state": cross_state,
                "observability_review_state": obs_state,
                "cross_band_summary_mode": cross_scope.get("bounded_summary_mode"),
                "observability_summary_mode": obs_scope.get("bounded_summary_mode"),
                "total_auditable_events": total_auditable,
                "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                "coverage_notes": (
                    list(cross_scope.get("coverage_notes", []))
                    + list(obs_scope.get("coverage_notes", []))
                ),
            },
            "evidence_counts": {
                "cross_band_total_auditable_events": cross_auditable,
                "observability_total_auditable_events": obs_auditable,
                "total_auditable_events": total_auditable,
                "cross_band_evidence_counts": cross_counts,
                "observability_evidence_counts": obs_counts,
            },
            "supporting_surfaces": {
                "cross_band_bounded_evidence_review": cross_review,
                "observability_bounded_evidence_review": observability_review,
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": [
                f"Review state: {review_state}",
                f"Review reason: {review_reason}",
                f"Bounded scope: {scope_label}",
                f"Cross-band bounded review state: {cross_state}",
                f"Observability bounded review state: {obs_state}",
                f"Total bounded auditable events: {total_auditable}",
                "System bounded evidence posture is scope-limited and not equivalent to full-range system evidence review.",
            ],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_evidence_review_sampler_window(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Bounded System Evidence Review Sampler v1.0 (index window).
        Read-only composition over bounded cross-band and bounded observability evidence-review surfaces.
        """
        cross_api_name = "get_cross_band_evidence_review_summary_window"
        obs_api_name = "get_observability_evidence_review_summary_window"

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            cross_surface,
            obs_surface,
            warnings: list[str],
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW_WINDOW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": reason,
                "window_spec": {},
                "evidence_scope": {
                    "bounded_scope": "INDEX_WINDOW",
                    "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "cross_band_total_auditable_events": 0,
                    "observability_total_auditable_events": 0,
                    "total_auditable_events": 0,
                    "cross_band_evidence_counts": {},
                    "observability_evidence_counts": {},
                },
                "supporting_surfaces": {
                    "cross_band_bounded_evidence_review": cross_surface,
                    "observability_bounded_evidence_review": obs_surface,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if not callable(getattr(self, cross_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required bounded system source surface missing: "
                    "get_cross_band_evidence_review_summary_window."
                ),
                cross_surface=None,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )
        if not callable(getattr(self, obs_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required bounded system source surface missing: "
                    "get_observability_evidence_review_summary_window."
                ),
                cross_surface=None,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        try:
            cross_review = self.get_cross_band_evidence_review_summary_window(
                start_index=start_index,
                end_index=end_index,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=(
                    "get_cross_band_evidence_review_summary_window() "
                    f"raised {type(exc).__name__}."
                ),
                cross_surface=None,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "CROSS_BAND_WINDOW_REVIEW_CALL_FAILED"],
            )

        try:
            obs_review = self.get_observability_evidence_review_summary_window(
                start_index=start_index,
                end_index=end_index,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=(
                    "get_observability_evidence_review_summary_window() "
                    f"raised {type(exc).__name__}."
                ),
                cross_surface=cross_review,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "OBSERVABILITY_WINDOW_REVIEW_CALL_FAILED"],
            )

        shape_ok = (
            isinstance(cross_review, dict)
            and cross_review.get("review_mode") == "CROSS_BAND_EVIDENCE_REVIEW_WINDOW"
            and isinstance(cross_review.get("window_spec"), dict)
            and isinstance(obs_review, dict)
            and obs_review.get("review_mode") == "OBSERVABILITY_EVIDENCE_REVIEW_WINDOW"
            and isinstance(obs_review.get("window_spec"), dict)
        )
        if not shape_ok:
            return _unavailable(
                reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Bounded system composition input surface shape/mode is invalid for index-window mapping.",
                cross_surface=cross_review,
                obs_surface=obs_review,
                warnings=["REQUIRED_SURFACE_SHAPE_INVALID"],
            )

        if cross_review.get("window_spec") != obs_review.get("window_spec"):
            return _unavailable(
                reason="WINDOW_SPEC_MISALIGNED",
                explanation="Bounded index-window review surfaces are misaligned; composition failed closed.",
                cross_surface=cross_review,
                obs_surface=obs_review,
                warnings=["WINDOW_SPEC_MISALIGNED"],
            )

        return self._build_system_bounded_evidence_review(
            cross_review=cross_review,
            observability_review=obs_review,
            review_mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            scope_label="INDEX_WINDOW",
        )

    def get_system_evidence_review_sampler_event_order_window(
        self,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Bounded System Evidence Review Sampler v1.0 (event-order window).
        Read-only composition over bounded cross-band and bounded observability evidence-review surfaces.
        """
        cross_api_name = "get_cross_band_evidence_review_summary_event_order_window"
        obs_api_name = "get_observability_evidence_review_summary_event_order_window"

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            cross_surface,
            obs_surface,
            warnings: list[str],
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": reason,
                "window_spec": {},
                "evidence_scope": {
                    "bounded_scope": "EVENT_ORDER_WINDOW",
                    "scope_equivalence": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "cross_band_total_auditable_events": 0,
                    "observability_total_auditable_events": 0,
                    "total_auditable_events": 0,
                    "cross_band_evidence_counts": {},
                    "observability_evidence_counts": {},
                },
                "supporting_surfaces": {
                    "cross_band_bounded_evidence_review": cross_surface,
                    "observability_bounded_evidence_review": obs_surface,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if not callable(getattr(self, cross_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required bounded system source surface missing: "
                    "get_cross_band_evidence_review_summary_event_order_window."
                ),
                cross_surface=None,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )
        if not callable(getattr(self, obs_api_name, None)):
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required bounded system source surface missing: "
                    "get_observability_evidence_review_summary_event_order_window."
                ),
                cross_surface=None,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        try:
            cross_review = self.get_cross_band_evidence_review_summary_event_order_window(
                start_event_order=start_event_order,
                end_event_order=end_event_order,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=(
                    "get_cross_band_evidence_review_summary_event_order_window() "
                    f"raised {type(exc).__name__}."
                ),
                cross_surface=None,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "CROSS_BAND_EVENT_ORDER_WINDOW_REVIEW_CALL_FAILED"],
            )

        try:
            obs_review = self.get_observability_evidence_review_summary_event_order_window(
                start_event_order=start_event_order,
                end_event_order=end_event_order,
                max_events=max_events,
            )
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=(
                    "get_observability_evidence_review_summary_event_order_window() "
                    f"raised {type(exc).__name__}."
                ),
                cross_surface=cross_review,
                obs_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "OBSERVABILITY_EVENT_ORDER_WINDOW_REVIEW_CALL_FAILED"],
            )

        shape_ok = (
            isinstance(cross_review, dict)
            and cross_review.get("review_mode") == "CROSS_BAND_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW"
            and isinstance(cross_review.get("window_spec"), dict)
            and isinstance(obs_review, dict)
            and obs_review.get("review_mode") == "OBSERVABILITY_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW"
            and isinstance(obs_review.get("window_spec"), dict)
        )
        if not shape_ok:
            return _unavailable(
                reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Bounded system composition input surface shape/mode is invalid for event-order mapping.",
                cross_surface=cross_review,
                obs_surface=obs_review,
                warnings=["REQUIRED_SURFACE_SHAPE_INVALID"],
            )

        if cross_review.get("window_spec") != obs_review.get("window_spec"):
            return _unavailable(
                reason="WINDOW_SPEC_MISALIGNED",
                explanation="Bounded event-order review surfaces are misaligned; composition failed closed.",
                cross_surface=cross_review,
                obs_surface=obs_review,
                warnings=["WINDOW_SPEC_MISALIGNED"],
            )

        return self._build_system_bounded_evidence_review(
            cross_review=cross_review,
            observability_review=obs_review,
            review_mode="SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            scope_label="EVENT_ORDER_WINDOW",
        )

    def _audit_system_evidence_review_sampler_stage_lock(
        self,
        *,
        sampler_api_name: str,
        cross_api_name: str,
        obs_api_name: str,
        audit_mode: str,
        scope_label: str,
        expected_sampler_mode: str,
        expected_cross_mode: str,
        expected_obs_mode: str,
        request_kwargs: dict,
    ) -> dict:
        _GUARDRAIL_FIELDS = [
            "lineage_mutation_performed",
            "event_creation_performed",
            "history_rewrite_performed",
        ]
        _FULL_RANGE_APIS = [
            "get_cross_band_evidence_review_summary",
            "get_observability_evidence_review_summary",
            "get_system_evidence_review_summary",
        ]

        def _check(name: str, passed: bool, reason: str, details: Optional[dict] = None) -> dict:
            return {
                "check_name": name,
                "passed": bool(passed),
                "reason": reason,
                "details": details if isinstance(details, dict) else {},
            }

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            sampler_surface,
            cross_surface,
            obs_surface,
        ) -> dict:
            return {
                "audit_available": False,
                "audit_mode": audit_mode,
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_UNAVAILABLE",
                "reason": reason,
                "check_results": [],
                "contract_surface": {
                    "required_surfaces": {
                        "sampler_api_present": callable(getattr(self, sampler_api_name, None)),
                        "cross_bounded_review_api_present": callable(getattr(self, cross_api_name, None)),
                        "observability_bounded_review_api_present": callable(getattr(self, obs_api_name, None)),
                    },
                    "scope_contract": {
                        "bounded_scope": scope_label,
                        "scope_equivalence_required": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                        "matching_mode_required": True,
                    },
                    "disallowed_full_range_posture_predicates": {
                        api_name: True for api_name in _FULL_RANGE_APIS
                    },
                },
                "supporting_surfaces": {
                    "system_evidence_review_sampler": sampler_surface,
                    "cross_band_bounded_evidence_review": cross_surface,
                    "observability_bounded_evidence_review": obs_surface,
                },
                "warnings": [],
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        missing = []
        if not callable(getattr(self, sampler_api_name, None)):
            missing.append(sampler_api_name)
        if not callable(getattr(self, cross_api_name, None)):
            missing.append(cross_api_name)
        if not callable(getattr(self, obs_api_name, None)):
            missing.append(obs_api_name)
        if missing:
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation="Required bounded sampler audit surface missing: " + ", ".join(missing) + ".",
                sampler_surface=None,
                cross_surface=None,
                obs_surface=None,
            )

        try:
            sampler_surface = getattr(self, sampler_api_name)(**request_kwargs)
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"{sampler_api_name}() raised {type(exc).__name__}.",
                sampler_surface=None,
                cross_surface=None,
                obs_surface=None,
            )

        try:
            cross_surface = getattr(self, cross_api_name)(**request_kwargs)
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"{cross_api_name}() raised {type(exc).__name__}.",
                sampler_surface=sampler_surface,
                cross_surface=None,
                obs_surface=None,
            )

        try:
            obs_surface = getattr(self, obs_api_name)(**request_kwargs)
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"{obs_api_name}() raised {type(exc).__name__}.",
                sampler_surface=sampler_surface,
                cross_surface=cross_surface,
                obs_surface=None,
            )

        checks: list[dict] = []
        warnings: list[str] = []

        sampler_shape_ok = (
            isinstance(sampler_surface, dict)
            and sampler_surface.get("review_mode") == expected_sampler_mode
            and isinstance(sampler_surface.get("review_state"), str)
            and isinstance(sampler_surface.get("review_reason"), str)
            and isinstance(sampler_surface.get("window_spec"), dict)
            and isinstance(sampler_surface.get("evidence_scope"), dict)
            and isinstance(sampler_surface.get("evidence_counts"), dict)
        )
        checks.append(
            _check(
                "SAMPLER_SURFACE_USABLE",
                sampler_shape_ok,
                "SAMPLER_SHAPE_OK" if sampler_shape_ok else "SAMPLER_SHAPE_INVALID",
                {"review_mode": sampler_surface.get("review_mode") if isinstance(sampler_surface, dict) else None},
            )
        )

        cross_shape_ok = (
            isinstance(cross_surface, dict)
            and cross_surface.get("review_mode") == expected_cross_mode
            and isinstance(cross_surface.get("window_spec"), dict)
            and isinstance(cross_surface.get("review_state"), str)
        )
        checks.append(
            _check(
                "CROSS_BOUNDED_ANCHOR_USABLE",
                cross_shape_ok,
                "CROSS_BOUNDED_SHAPE_OK" if cross_shape_ok else "CROSS_BOUNDED_SHAPE_INVALID",
                {"review_mode": cross_surface.get("review_mode") if isinstance(cross_surface, dict) else None},
            )
        )

        obs_shape_ok = (
            isinstance(obs_surface, dict)
            and obs_surface.get("review_mode") == expected_obs_mode
            and isinstance(obs_surface.get("window_spec"), dict)
            and isinstance(obs_surface.get("review_state"), str)
        )
        checks.append(
            _check(
                "OBSERVABILITY_BOUNDED_ANCHOR_USABLE",
                obs_shape_ok,
                "OBS_BOUNDED_SHAPE_OK" if obs_shape_ok else "OBS_BOUNDED_SHAPE_INVALID",
                {"review_mode": obs_surface.get("review_mode") if isinstance(obs_surface, dict) else None},
            )
        )

        if not (sampler_shape_ok and cross_shape_ok and obs_shape_ok):
            checks_failed = sum(1 for c in checks if c.get("passed") is False)
            return {
                "audit_available": True,
                "audit_mode": audit_mode,
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT",
                "reason": "CHECK_FAILURES_DETECTED",
                "check_results": checks,
                "contract_surface": {
                    "required_surfaces": {
                        "sampler_api_present": True,
                        "cross_bounded_review_api_present": True,
                        "observability_bounded_review_api_present": True,
                    },
                    "scope_contract": {
                        "bounded_scope": scope_label,
                        "scope_equivalence_required": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                        "matching_mode_required": True,
                    },
                    "disallowed_full_range_posture_predicates": {
                        api_name: True for api_name in _FULL_RANGE_APIS
                    },
                    "checks_run": len(checks),
                    "checks_failed": checks_failed,
                },
                "supporting_surfaces": {
                    "system_evidence_review_sampler": sampler_surface,
                    "cross_band_bounded_evidence_review": cross_surface,
                    "observability_bounded_evidence_review": obs_surface,
                },
                "warnings": warnings,
                "explanation_lines": ["Sampler/anchor surface shape invalid for bounded stage-lock audit."],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        cross_spec = cross_surface.get("window_spec", {})
        obs_spec = obs_surface.get("window_spec", {})
        sampler_spec = sampler_surface.get("window_spec", {})
        anchors_aligned = cross_spec == obs_spec
        sampler_matches_anchors = sampler_spec == cross_spec
        checks.append(
            _check(
                "MATCHING_WINDOW_SPEC_ACROSS_BOUNDED_INPUTS",
                anchors_aligned,
                "WINDOW_SPECS_ALIGNED" if anchors_aligned else "WINDOW_SPECS_MISALIGNED",
                {"cross_window_spec": cross_spec, "observability_window_spec": obs_spec},
            )
        )
        checks.append(
            _check(
                "SAMPLER_WINDOW_SPEC_MATCHES_INPUTS",
                sampler_matches_anchors,
                "SAMPLER_WINDOW_SPEC_MATCHED" if sampler_matches_anchors else "SAMPLER_WINDOW_SPEC_MISMATCH",
                {"sampler_window_spec": sampler_spec, "anchor_window_spec": cross_spec},
            )
        )

        scope = sampler_surface.get("evidence_scope", {})
        scope_non_equivalent = (
            isinstance(scope, dict)
            and scope.get("scope_equivalence") == "BOUNDED_NOT_FULL_RANGE_EQUIVALENT"
        )
        checks.append(
            _check(
                "BOUNDED_SCOPE_NON_EQUIVALENCE_EXPLICIT",
                scope_non_equivalent,
                "SCOPE_NON_EQUIVALENCE_EXPLICIT"
                if scope_non_equivalent
                else "SCOPE_NON_EQUIVALENCE_MISSING_OR_DRIFTED",
                {"scope_equivalence": scope.get("scope_equivalence") if isinstance(scope, dict) else None},
            )
        )

        guardrails_ok = all(sampler_surface.get(flag) is False for flag in _GUARDRAIL_FIELDS)
        checks.append(
            _check(
                "READ_ONLY_GUARDRAILS_FALSE",
                guardrails_ok,
                "GUARDRAILS_FALSE" if guardrails_ok else "GUARDRAIL_FLAG_DRIFT_DETECTED",
                {flag: sampler_surface.get(flag) for flag in _GUARDRAIL_FIELDS},
            )
        )

        # Validate fail-closed behavior for window-spec misalignment regression.
        fail_closed_ok = False
        fail_closed_details = {}
        original_obs_api = getattr(self, obs_api_name)
        try:
            def _misaligned_obs(**kwargs):
                out = original_obs_api(**kwargs)
                if isinstance(out, dict):
                    mutated = dict(out)
                    ws = mutated.get("window_spec", {})
                    if isinstance(ws, dict):
                        ws2 = dict(ws)
                        if scope_label == "INDEX_WINDOW":
                            ws2["applied_end_index"] = (
                                int(ws2.get("applied_end_index", 0))
                                + 1
                                if isinstance(ws2.get("applied_end_index"), int)
                                else 1
                            )
                        else:
                            ws2["applied_end_event_order"] = (
                                float(ws2.get("applied_end_event_order", 0.0)) + 1.0
                                if isinstance(ws2.get("applied_end_event_order"), (int, float))
                                else 1.0
                            )
                        mutated["window_spec"] = ws2
                    return mutated
                return out

            setattr(self, obs_api_name, _misaligned_obs)
            drift_out = getattr(self, sampler_api_name)(**request_kwargs)
            if isinstance(drift_out, dict):
                fail_closed_ok = (
                    drift_out.get("review_state") == "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
                    and drift_out.get("review_reason") == "WINDOW_SPEC_MISALIGNED"
                )
                fail_closed_details = {
                    "drift_review_state": drift_out.get("review_state"),
                    "drift_review_reason": drift_out.get("review_reason"),
                }
        except Exception as exc:
            fail_closed_ok = False
            fail_closed_details = {"exception": type(exc).__name__}
        finally:
            setattr(self, obs_api_name, original_obs_api)

        checks.append(
            _check(
                "FAIL_CLOSED_ON_WINDOW_SPEC_MISALIGNMENT",
                fail_closed_ok,
                "FAIL_CLOSED_BEHAVIOR_PRESERVED"
                if fail_closed_ok
                else "FAIL_CLOSED_BEHAVIOR_DRIFTED",
                fail_closed_details,
            )
        )

        # Full-range surfaces are context-only and must never act as bounded posture predicates.
        full_range_non_predicate_ok = False
        full_range_details = {}
        original_full_range = {}
        try:
            baseline_state = sampler_surface.get("review_state")
            baseline_reason = sampler_surface.get("review_reason")
            for api_name in _FULL_RANGE_APIS:
                original_full_range[api_name] = getattr(self, api_name, None)

                def _raise_forbidden(*_args, **_kwargs):
                    raise AssertionError("FORBIDDEN_FULL_RANGE_DEPENDENCY")

                setattr(self, api_name, _raise_forbidden)

            probe_out = getattr(self, sampler_api_name)(**request_kwargs)
            if isinstance(probe_out, dict):
                full_range_non_predicate_ok = (
                    probe_out.get("review_state") == baseline_state
                    and probe_out.get("review_reason") == baseline_reason
                )
                full_range_details = {
                    "baseline_state": baseline_state,
                    "probe_state": probe_out.get("review_state"),
                    "baseline_reason": baseline_reason,
                    "probe_reason": probe_out.get("review_reason"),
                }
        except Exception as exc:
            full_range_non_predicate_ok = False
            full_range_details = {"exception": type(exc).__name__}
        finally:
            for api_name, original_fn in original_full_range.items():
                setattr(self, api_name, original_fn)

        checks.append(
            _check(
                "FULL_RANGE_SURFACES_CONTEXT_ONLY_NON_PREDICATE",
                full_range_non_predicate_ok,
                "NO_FULL_RANGE_PREDICATE_LEAKAGE"
                if full_range_non_predicate_ok
                else "FULL_RANGE_PREDICATE_LEAKAGE_DETECTED",
                full_range_details,
            )
        )

        checks_failed = sum(1 for c in checks if c.get("passed") is False)
        checks_passed = sum(1 for c in checks if c.get("passed") is True)
        if checks_failed == 0:
            lock_state = "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_LOCKED"
            reason = "ALL_CONSISTENCY_CHECKS_PASSED"
        else:
            lock_state = "SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_INCONSISTENT"
            reason = "CHECK_FAILURES_DETECTED"
            warnings.append("SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_CHECK_FAILURES")

        return {
            "audit_available": True,
            "audit_mode": audit_mode,
            "lock_state": lock_state,
            "reason": reason,
            "check_results": checks,
            "contract_surface": {
                "required_surfaces": {
                    "sampler_api_present": True,
                    "cross_bounded_review_api_present": True,
                    "observability_bounded_review_api_present": True,
                },
                "allowed_audited_surfaces_only": [
                    sampler_api_name,
                    cross_api_name,
                    obs_api_name,
                ],
                "scope_contract": {
                    "bounded_scope": scope_label,
                    "scope_equivalence_required": "BOUNDED_NOT_FULL_RANGE_EQUIVALENT",
                    "matching_mode_required": True,
                },
                "disallowed_full_range_posture_predicates": {
                    api_name: True for api_name in _FULL_RANGE_APIS
                },
                "checks_run": len(checks),
                "checks_passed": checks_passed,
                "checks_failed": checks_failed,
            },
            "supporting_surfaces": {
                "system_evidence_review_sampler": sampler_surface,
                "cross_band_bounded_evidence_review": cross_surface,
                "observability_bounded_evidence_review": obs_surface,
            },
            "warnings": sorted(
                set(
                    warnings
                    + list(sampler_surface.get("warnings", []))
                    + list(cross_surface.get("warnings", []))
                    + list(obs_surface.get("warnings", []))
                )
            ),
            "explanation_lines": [
                f"Sampler bounded stage-lock state: {lock_state}",
                f"Sampler bounded stage-lock reason: {reason}",
                f"Bounded scope audited: {scope_label}",
                f"Checks passed/failed: {checks_passed}/{checks_failed}",
            ],
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_evidence_review_sampler_stage_lock_window(
        self,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Bounded System Evidence Review Consistency / Stage Lock v1.1 (index window).
        Read-only contract freeze/audit over bounded system sampler index-window composition.
        """
        return self._audit_system_evidence_review_sampler_stage_lock(
            sampler_api_name="get_system_evidence_review_sampler_window",
            cross_api_name="get_cross_band_evidence_review_summary_window",
            obs_api_name="get_observability_evidence_review_summary_window",
            audit_mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_WINDOW",
            scope_label="INDEX_WINDOW",
            expected_sampler_mode="SYSTEM_EVIDENCE_REVIEW_WINDOW",
            expected_cross_mode="CROSS_BAND_EVIDENCE_REVIEW_WINDOW",
            expected_obs_mode="OBSERVABILITY_EVIDENCE_REVIEW_WINDOW",
            request_kwargs={
                "start_index": start_index,
                "end_index": end_index,
                "max_events": max_events,
            },
        )

    def get_system_evidence_review_sampler_stage_lock_event_order_window(
        self,
        start_event_order: Optional[float] = None,
        end_event_order: Optional[float] = None,
        max_events: Optional[int] = None,
    ) -> dict:
        """
        Bounded System Evidence Review Consistency / Stage Lock v1.1 (event-order window).
        Read-only contract freeze/audit over bounded system sampler event-order composition.
        """
        return self._audit_system_evidence_review_sampler_stage_lock(
            sampler_api_name="get_system_evidence_review_sampler_event_order_window",
            cross_api_name="get_cross_band_evidence_review_summary_event_order_window",
            obs_api_name="get_observability_evidence_review_summary_event_order_window",
            audit_mode="SYSTEM_EVIDENCE_REVIEW_SAMPLER_STAGE_LOCK_EVENT_ORDER_WINDOW",
            scope_label="EVENT_ORDER_WINDOW",
            expected_sampler_mode="SYSTEM_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            expected_cross_mode="CROSS_BAND_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            expected_obs_mode="OBSERVABILITY_EVIDENCE_REVIEW_EVENT_ORDER_WINDOW",
            request_kwargs={
                "start_event_order": start_event_order,
                "end_event_order": end_event_order,
                "max_events": max_events,
            },
        )

    def get_observability_evidence_review_summary(self) -> dict:
        """
        Observability Evidence Review Summary v1.0.
        Read-only observability-side evidence review composed only from locked observability outputs.
        """
        required_api_names = [
            "get_pressure_capture_quality_summary",
            "get_observability_stage_lock_audit",
        ]

        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        def _unavailable(
            *,
            review_reason: str,
            explanation: str,
            warnings: list[str],
            quality_surface,
            stage_lock_surface,
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
                "review_state": "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": review_reason,
                "supporting_surfaces": {
                    "observability_pressure_capture_quality_summary": quality_surface,
                    "observability_stage_lock_audit": stage_lock_surface,
                },
                "evidence_scope": {
                    "stage_lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                    "stage_lock_reason": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                    "quality_summary_available": False,
                    "quality_summary_mode": "UNAVAILABLE",
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "total_transition_events": 0,
                    "total_auditable_events": 0,
                    "pressure_snapshot_present_count": 0,
                    "pressure_snapshot_missing_count": 0,
                    "audit_state_counts": {
                        "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                    },
                    "capture_reason_counts": {
                        "PRESSURE_CAPTURE_FULL": 0,
                        "PRESSURE_CAPTURE_PARTIAL": 0,
                        "PRESSURE_CAPTURE_FAILED": 0,
                        "UNRECOGNIZED_CAPTURE_REASON": 0,
                    },
                    "recoverability_counts": {
                        "FULLY_RECOVERABLE": 0,
                        "PARTIALLY_RECOVERABLE": 0,
                        "UNRECOVERABLE": 0,
                    },
                    "event_type_counts": {},
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        missing_required = [
            name for name in required_api_names if not callable(getattr(self, name, None))
        ]
        if missing_required:
            return _unavailable(
                review_reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required observability evidence-review surfaces missing: "
                    + ", ".join(missing_required)
                    + "."
                ),
                warnings=["REQUIRED_SURFACE_MISSING"],
                quality_surface=None,
                stage_lock_surface=None,
            )

        quality_summary = None
        stage_lock_audit = None

        try:
            quality_summary = self.get_pressure_capture_quality_summary()
        except Exception as exc:
            return _unavailable(
                review_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_pressure_capture_quality_summary() raised {type(exc).__name__}.",
                warnings=["REQUIRED_SURFACE_UNUSABLE", "OBSERVABILITY_QUALITY_SURFACE_CALL_FAILED"],
                quality_surface=None,
                stage_lock_surface=None,
            )

        try:
            stage_lock_audit = self.get_observability_stage_lock_audit()
        except Exception as exc:
            return _unavailable(
                review_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_observability_stage_lock_audit() raised {type(exc).__name__}.",
                warnings=["REQUIRED_SURFACE_UNUSABLE", "OBSERVABILITY_STAGE_LOCK_SURFACE_CALL_FAILED"],
                quality_surface=quality_summary,
                stage_lock_surface=None,
            )

        quality_shape_ok = isinstance(quality_summary, dict)
        stage_lock_shape_ok = (
            isinstance(stage_lock_audit, dict)
            and isinstance(stage_lock_audit.get("lock_state"), str)
        )
        if not quality_shape_ok or not stage_lock_shape_ok:
            bad = []
            if not quality_shape_ok:
                bad.append("OBSERVABILITY_QUALITY_SURFACE_SHAPE_INVALID")
            if not stage_lock_shape_ok:
                bad.append("OBSERVABILITY_STAGE_LOCK_SURFACE_SHAPE_INVALID")
            return _unavailable(
                review_reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Required observability evidence-review surface shape invalid: " + ", ".join(bad) + ".",
                warnings=bad,
                quality_surface=quality_summary,
                stage_lock_surface=stage_lock_audit,
            )

        stage_lock_state = str(stage_lock_audit.get("lock_state", "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"))
        stage_lock_reason = str(stage_lock_audit.get("reason", "OBSERVABILITY_STAGE_LOCK_REASON_MISSING"))
        stage_lock_available = bool(stage_lock_audit.get("audit_available", False))

        quality_available = bool(quality_summary.get("summary_available", False))
        quality_mode = str(quality_summary.get("summary_mode", "UNAVAILABLE"))
        quality_reason = str(quality_summary.get("reason", "OBSERVABILITY_QUALITY_REASON_MISSING"))
        total_transition = _as_int(quality_summary.get("total_transition_events", 0))
        auditable = _as_int(quality_summary.get("auditable_event_count", 0))
        snapshot_present = _as_int(quality_summary.get("pressure_snapshot_present_count", 0))
        snapshot_missing = _as_int(quality_summary.get("pressure_snapshot_missing_count", 0))

        audit_state_counts = (
            dict(quality_summary.get("audit_state_counts", {}))
            if isinstance(quality_summary.get("audit_state_counts"), dict)
            else {
                "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
            }
        )
        capture_reason_counts = (
            dict(quality_summary.get("capture_reason_counts", {}))
            if isinstance(quality_summary.get("capture_reason_counts"), dict)
            else {
                "PRESSURE_CAPTURE_FULL": 0,
                "PRESSURE_CAPTURE_PARTIAL": 0,
                "PRESSURE_CAPTURE_FAILED": 0,
                "UNRECOGNIZED_CAPTURE_REASON": 0,
            }
        )
        recoverability_counts = (
            dict(quality_summary.get("recoverability_counts", {}))
            if isinstance(quality_summary.get("recoverability_counts"), dict)
            else {
                "FULLY_RECOVERABLE": 0,
                "PARTIALLY_RECOVERABLE": 0,
                "UNRECOVERABLE": 0,
            }
        )
        event_type_counts = (
            dict(quality_summary.get("event_type_counts", {}))
            if isinstance(quality_summary.get("event_type_counts"), dict)
            else {}
        )

        valid_count = _as_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_VALID", 0))
        invalid_count = _as_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_INVALID", 0))
        unavailable_count = _as_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_UNAVAILABLE", 0))

        meaningful_evidence_exists = auditable > 0
        ready = (
            quality_available
            and stage_lock_available
            and stage_lock_state == "OBSERVABILITY_STAGE_LOCKED"
            and meaningful_evidence_exists
            and invalid_count == 0
            and unavailable_count == 0
        )

        if ready:
            review_state = "OBSERVABILITY_EVIDENCE_REVIEW_READY"
            review_reason = "LOCKED_WITH_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE"
        elif meaningful_evidence_exists and (quality_available or stage_lock_available):
            review_state = "OBSERVABILITY_EVIDENCE_REVIEW_PARTIAL"
            review_reason = "LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE"
        else:
            review_state = "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
            review_reason = "OBSERVABILITY_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING"

        warnings = []
        warnings.extend(quality_summary.get("warnings", []))
        warnings.extend(stage_lock_audit.get("warnings", []))

        supporting_surfaces = {
            "observability_pressure_capture_quality_summary": quality_summary,
            "observability_stage_lock_audit": stage_lock_audit,
        }

        evidence_scope = {
            "stage_lock_state": stage_lock_state,
            "stage_lock_reason": stage_lock_reason,
            "quality_summary_available": quality_available,
            "quality_summary_mode": quality_mode,
            "quality_summary_reason": quality_reason,
            "coverage_notes": (
                list(quality_summary.get("explanation_lines", []))
                + list(stage_lock_audit.get("explanation_lines", []))
            ),
        }
        evidence_counts = {
            "total_transition_events": total_transition,
            "total_auditable_events": auditable,
            "pressure_snapshot_present_count": snapshot_present,
            "pressure_snapshot_missing_count": snapshot_missing,
            "audit_state_counts": audit_state_counts,
            "capture_reason_counts": capture_reason_counts,
            "recoverability_counts": recoverability_counts,
            "event_type_counts": event_type_counts,
        }

        explanation_lines = [
            f"Review state: {review_state}",
            f"Review reason: {review_reason}",
            f"Observability stage lock: {stage_lock_state}",
            f"Auditable events: {auditable}",
            f"Audit valid/invalid/unavailable: {valid_count}/{invalid_count}/{unavailable_count}",
        ]
        if auditable == 0:
            explanation_lines.append("No auditable observability evidence events are currently available.")

        return {
            "review_available": True,
            "review_mode": "OBSERVABILITY_EVIDENCE_REVIEW",
            "review_state": review_state,
            "review_reason": review_reason,
            "supporting_surfaces": supporting_surfaces,
            "evidence_scope": evidence_scope,
            "evidence_counts": evidence_counts,
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_observability_evidence_review_stage_lock_audit(self) -> dict:
        """
        Observability Evidence Review Consistency / Stage Lock v1.1.
        Read-only audit over observability evidence-review contract and its allowed source surfaces.
        """
        _OBS_REVIEW_API = "get_observability_evidence_review_summary"
        _QUALITY_API = "get_pressure_capture_quality_summary"
        _OBS_STAGE_API = "get_observability_stage_lock_audit"
        _GUARDRAIL_FIELDS = [
            "lineage_mutation_performed",
            "event_creation_performed",
            "history_rewrite_performed",
        ]

        def _safe_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        def _check(name: str, passed: bool, reason: str, details: Optional[dict] = None) -> dict:
            return {
                "check_name": name,
                "passed": bool(passed),
                "reason": reason,
                "details": details if isinstance(details, dict) else {},
            }

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            review_surface,
            quality_surface,
            stage_lock_surface,
        ) -> dict:
            return {
                "audit_available": False,
                "audit_mode": "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE",
                "reason": reason,
                "check_results": [],
                "contract_surface": {
                    "required_surfaces": {
                        "observability_evidence_review_api_present": callable(getattr(self, _OBS_REVIEW_API, None)),
                        "pressure_capture_quality_summary_api_present": callable(getattr(self, _QUALITY_API, None)),
                        "observability_stage_lock_api_present": callable(getattr(self, _OBS_STAGE_API, None)),
                    },
                    "allowed_audited_surfaces_only": [
                        _OBS_REVIEW_API,
                        _QUALITY_API,
                        _OBS_STAGE_API,
                    ],
                    "frozen_review_mapping": {
                        "ready_reason": "LOCKED_WITH_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE",
                        "partial_reason": "LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE",
                        "unavailable_reason": "OBSERVABILITY_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING",
                    },
                },
                "supporting_surfaces": {
                    "observability_evidence_review_summary": review_surface,
                    "observability_pressure_capture_quality_summary": quality_surface,
                    "observability_stage_lock_audit": stage_lock_surface,
                },
                "warnings": [],
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        required_missing = []
        if not callable(getattr(self, _OBS_REVIEW_API, None)):
            required_missing.append(_OBS_REVIEW_API)
        if not callable(getattr(self, _QUALITY_API, None)):
            required_missing.append(_QUALITY_API)
        if not callable(getattr(self, _OBS_STAGE_API, None)):
            required_missing.append(_OBS_STAGE_API)
        if required_missing:
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required observability evidence-review stage-lock surface missing: "
                    + ", ".join(required_missing)
                    + "."
                ),
                review_surface=None,
                quality_surface=None,
                stage_lock_surface=None,
            )

        try:
            review_surface = self.get_observability_evidence_review_summary()
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_observability_evidence_review_summary() raised {type(exc).__name__}.",
                review_surface=None,
                quality_surface=None,
                stage_lock_surface=None,
            )
        try:
            quality_surface = self.get_pressure_capture_quality_summary()
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_pressure_capture_quality_summary() raised {type(exc).__name__}.",
                review_surface=review_surface,
                quality_surface=None,
                stage_lock_surface=None,
            )
        try:
            stage_lock_surface = self.get_observability_stage_lock_audit()
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_observability_stage_lock_audit() raised {type(exc).__name__}.",
                review_surface=review_surface,
                quality_surface=quality_surface,
                stage_lock_surface=None,
            )

        checks: list[dict] = []
        warnings: list[str] = []

        review_shape_ok = (
            isinstance(review_surface, dict)
            and review_surface.get("review_mode") == "OBSERVABILITY_EVIDENCE_REVIEW"
            and isinstance(review_surface.get("review_state"), str)
            and isinstance(review_surface.get("review_reason"), str)
            and isinstance(review_surface.get("evidence_counts", {}), dict)
            and isinstance(review_surface.get("evidence_scope", {}), dict)
        )
        checks.append(
            _check(
                "OBSERVABILITY_REVIEW_SURFACE_USABLE",
                review_shape_ok,
                "REVIEW_SURFACE_OK" if review_shape_ok else "REVIEW_SURFACE_SHAPE_UNEXPECTED",
                {"review_surface_type": type(review_surface).__name__},
            )
        )

        quality_shape_ok = (
            isinstance(quality_surface, dict)
            and isinstance(quality_surface.get("summary_available", False), bool)
            and isinstance(quality_surface.get("audit_state_counts", {}), dict)
            and isinstance(quality_surface.get("capture_reason_counts", {}), dict)
            and isinstance(quality_surface.get("recoverability_counts", {}), dict)
        )
        checks.append(
            _check(
                "QUALITY_SOURCE_SURFACE_USABLE",
                quality_shape_ok,
                "QUALITY_SURFACE_OK" if quality_shape_ok else "QUALITY_SURFACE_SHAPE_UNEXPECTED",
                {"quality_surface_type": type(quality_surface).__name__},
            )
        )

        stage_lock_shape_ok = (
            isinstance(stage_lock_surface, dict)
            and stage_lock_surface.get("audit_mode") == "OBSERVABILITY_STAGE_LOCK"
            and isinstance(stage_lock_surface.get("lock_state"), str)
            and isinstance(stage_lock_surface.get("reason"), str)
        )
        checks.append(
            _check(
                "OBSERVABILITY_STAGE_LOCK_SOURCE_USABLE",
                stage_lock_shape_ok,
                "STAGE_LOCK_SURFACE_OK" if stage_lock_shape_ok else "STAGE_LOCK_SURFACE_SHAPE_UNEXPECTED",
                {"stage_lock_surface_type": type(stage_lock_surface).__name__},
            )
        )

        if review_shape_ok and quality_shape_ok and stage_lock_shape_ok:
            quality_available = bool(quality_surface.get("summary_available", False))
            stage_lock_available = bool(stage_lock_surface.get("audit_available", False))
            stage_lock_state = str(
                stage_lock_surface.get("lock_state", "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE")
            )
            auditable = _safe_int(quality_surface.get("auditable_event_count", 0))
            audit_state_counts = (
                quality_surface.get("audit_state_counts", {})
                if isinstance(quality_surface.get("audit_state_counts"), dict)
                else {}
            )
            invalid_count = _safe_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_INVALID", 0))
            unavailable_count = _safe_int(audit_state_counts.get("PRESSURE_CAPTURE_AUDIT_UNAVAILABLE", 0))

            ready_expected = (
                quality_available
                and stage_lock_available
                and stage_lock_state == "OBSERVABILITY_STAGE_LOCKED"
                and auditable > 0
                and invalid_count == 0
                and unavailable_count == 0
            )
            if ready_expected:
                expected_state = "OBSERVABILITY_EVIDENCE_REVIEW_READY"
                expected_reason = "LOCKED_WITH_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE"
            elif auditable > 0 and (quality_available or stage_lock_available):
                expected_state = "OBSERVABILITY_EVIDENCE_REVIEW_PARTIAL"
                expected_reason = "LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE"
            else:
                expected_state = "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
                expected_reason = "OBSERVABILITY_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING"

            observed_state = str(review_surface.get("review_state", "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"))
            observed_reason = str(review_surface.get("review_reason", "OBSERVABILITY_EVIDENCE_REVIEW_REASON_MISSING"))

            checks.append(
                _check(
                    "REVIEW_STATE_REASON_MATCH_ALLOWED_MAPPING",
                    observed_state == expected_state and observed_reason == expected_reason,
                    "STATE_REASON_MATCH" if observed_state == expected_state and observed_reason == expected_reason else "STATE_REASON_DRIFT",
                    {
                        "expected_state": expected_state,
                        "observed_state": observed_state,
                        "expected_reason": expected_reason,
                        "observed_reason": observed_reason,
                    },
                )
            )

            review_counts = (
                review_surface.get("evidence_counts", {})
                if isinstance(review_surface.get("evidence_counts"), dict)
                else {}
            )
            quality_count_match = (
                _safe_int(review_counts.get("total_transition_events", -1))
                == _safe_int(quality_surface.get("total_transition_events", -2))
                and _safe_int(review_counts.get("total_auditable_events", -1))
                == _safe_int(quality_surface.get("auditable_event_count", -2))
                and _safe_int(review_counts.get("pressure_snapshot_present_count", -1))
                == _safe_int(quality_surface.get("pressure_snapshot_present_count", -2))
                and _safe_int(review_counts.get("pressure_snapshot_missing_count", -1))
                == _safe_int(quality_surface.get("pressure_snapshot_missing_count", -2))
                and review_counts.get("audit_state_counts", {}) == quality_surface.get("audit_state_counts", {})
                and review_counts.get("capture_reason_counts", {}) == quality_surface.get("capture_reason_counts", {})
                and review_counts.get("recoverability_counts", {}) == quality_surface.get("recoverability_counts", {})
            )
            checks.append(
                _check(
                    "QUALITY_COUNTS_COMPOSED_HONESTLY",
                    quality_count_match,
                    "QUALITY_COUNTS_MATCH" if quality_count_match else "QUALITY_COUNTS_DRIFT",
                    {},
                )
            )

            scope = review_surface.get("evidence_scope", {})
            if not isinstance(scope, dict):
                scope = {}
            no_cross_or_system_keys = (
                "cross_band_review_state" not in scope
                and "cross_band_stage_lock_state" not in scope
                and "system_gate_state" not in scope
            )
            supporting = review_surface.get("supporting_surfaces", {})
            if not isinstance(supporting, dict):
                supporting = {}
            no_cross_or_system_support = (
                "cross_band_evidence_review_summary" not in supporting
                and "system_lock_gate_posture" not in supporting
            )
            checks.append(
                _check(
                    "NO_HIDDEN_CROSS_BAND_OR_SYSTEM_GATE_DEPENDENCY",
                    no_cross_or_system_keys and no_cross_or_system_support,
                    "NO_HIDDEN_CROSS_SYSTEM_CONTEXT"
                    if no_cross_or_system_keys and no_cross_or_system_support
                    else "HIDDEN_CROSS_SYSTEM_CONTEXT_DETECTED",
                    {},
                )
            )

        guardrail_violations = []
        for surface_name, surface_payload in [
            ("observability_evidence_review_summary", review_surface),
            ("observability_pressure_capture_quality_summary", quality_surface),
            ("observability_stage_lock_audit", stage_lock_surface),
        ]:
            if not isinstance(surface_payload, dict):
                continue
            for key in _GUARDRAIL_FIELDS:
                if surface_payload.get(key) is not False:
                    guardrail_violations.append(f"{surface_name}:{key}")
        checks.append(
            _check(
                "READ_ONLY_GUARDRAILS_FALSE",
                len(guardrail_violations) == 0,
                "ALL_GUARDRAILS_FALSE" if len(guardrail_violations) == 0 else "GUARDRAIL_FLAG_VIOLATION",
                {"violations": guardrail_violations},
            )
        )
        if guardrail_violations:
            warnings.append("READ_ONLY_GUARDRAIL_VIOLATION_DETECTED")

        checks_failed = sum(1 for c in checks if c.get("passed") is False)
        checks_passed = len(checks) - checks_failed

        if checks_failed == 0:
            lock_state = "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCKED"
            reason = "ALL_CONSISTENCY_CHECKS_PASSED"
            explanation_lines = [
                "Observability evidence-review stage-lock checks passed."
            ]
        else:
            lock_state = "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
            reason = "CONSISTENCY_CHECK_FAILED"
            failed = [c["check_name"] for c in checks if c.get("passed") is False]
            explanation_lines = [
                "Observability evidence-review stage-lock inconsistency detected.",
                "Failed checks: " + ", ".join(failed),
            ]

        warnings.extend(review_surface.get("warnings", []) if isinstance(review_surface, dict) else [])
        warnings.extend(quality_surface.get("warnings", []) if isinstance(quality_surface, dict) else [])
        warnings.extend(stage_lock_surface.get("warnings", []) if isinstance(stage_lock_surface, dict) else [])

        return {
            "audit_available": True,
            "audit_mode": "OBSERVABILITY_EVIDENCE_REVIEW_STAGE_LOCK",
            "lock_state": lock_state,
            "reason": reason,
            "check_results": checks,
            "contract_surface": {
                "required_surfaces": {
                    "observability_evidence_review_api_present": True,
                    "pressure_capture_quality_summary_api_present": True,
                    "observability_stage_lock_api_present": True,
                },
                "allowed_audited_surfaces_only": [
                    _OBS_REVIEW_API,
                    _QUALITY_API,
                    _OBS_STAGE_API,
                ],
                "frozen_review_mapping": {
                    "ready_reason": "LOCKED_WITH_FULLY_AUDITABLE_OBSERVABILITY_EVIDENCE",
                    "partial_reason": "LIMITED_OR_MIXED_OBSERVABILITY_EVIDENCE",
                    "unavailable_reason": "OBSERVABILITY_EVIDENCE_SURFACE_INSUFFICIENT_OR_MISSING",
                },
                "disallowed_hidden_context": {
                    "cross_band_evidence_review_summary": True,
                    "system_lock_gate_posture": True,
                },
            },
            "supporting_surfaces": {
                "observability_evidence_review_summary": review_surface,
                "observability_pressure_capture_quality_summary": quality_surface,
                "observability_stage_lock_audit": stage_lock_surface,
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_evidence_review_summary(self) -> dict:
        """
        Implementation of System-Wide Evidence Review v1.1.
        Strictly read-only composition layer over completed lower-band evidence surfaces.
        """
        required_api_names = [
            "get_cross_band_evidence_review_summary",
            "get_system_lock_gate_posture",
        ]

        def _as_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        def _unavailable(
            *,
            review_reason: str,
            explanation: str,
            warnings: list[str],
            cross_band_surface,
            system_lock_surface,
            observability_stage_surface,
            observability_quality_surface,
            observability_review_surface,
        ) -> dict:
            return {
                "review_available": False,
                "review_mode": "SYSTEM_EVIDENCE_REVIEW",
                "review_state": "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
                "review_reason": review_reason,
                "system_lock_posture": system_lock_surface,
                "supporting_surfaces": {
                    "cross_band_evidence_review_summary": cross_band_surface,
                    "observability_stage_lock_audit": observability_stage_surface,
                    "observability_pressure_capture_quality_summary": observability_quality_surface,
                    "observability_evidence_review_summary": observability_review_surface,
                    "system_lock_gate_posture": system_lock_surface,
                },
                "evidence_scope": {
                    "cross_band_review_state": "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE",
                    "cross_band_stage_lock_state": "CROSS_BAND_STAGE_LOCK_UNAVAILABLE",
                    "observability_stage_lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                    "system_gate_state": "SYSTEM_GATE_UNAVAILABLE",
                    "observability_review_surface_present": bool(observability_review_surface),
                    "coverage_notes": [explanation],
                },
                "evidence_counts": {
                    "cross_band_total_auditable_events": 0,
                    "observability_total_auditable_events": 0,
                    "total_auditable_events": 0,
                    "cross_band_self_check_state_counts": {
                        "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                        "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                        "CROSS_BAND_PARTIAL": 0,
                        "CROSS_BAND_UNAVAILABLE": 0,
                    },
                    "observability_audit_state_counts": {
                        "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                        "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                    },
                    "observability_recoverability_counts": {
                        "FULLY_RECOVERABLE": 0,
                        "PARTIALLY_RECOVERABLE": 0,
                        "UNRECOVERABLE": 0,
                    },
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        missing_required = [
            name for name in required_api_names if not callable(getattr(self, name, None))
        ]
        if missing_required:
            return _unavailable(
                review_reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required system evidence-review composition surfaces missing: "
                    + ", ".join(missing_required)
                    + "."
                ),
                warnings=["REQUIRED_SURFACE_MISSING"],
                cross_band_surface=None,
                system_lock_surface=None,
                observability_stage_surface=None,
                observability_quality_surface=None,
                observability_review_surface=None,
            )

        cross_band_summary = None
        system_lock_posture = None
        observability_stage_lock = None
        observability_quality_summary = None
        observability_review_summary = None

        try:
            cross_band_summary = self.get_cross_band_evidence_review_summary()
        except Exception as exc:
            return _unavailable(
                review_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_cross_band_evidence_review_summary() raised {type(exc).__name__}.",
                warnings=["REQUIRED_SURFACE_UNUSABLE", "CROSS_BAND_SURFACE_CALL_FAILED"],
                cross_band_surface=None,
                system_lock_surface=None,
                observability_stage_surface=None,
                observability_quality_surface=None,
                observability_review_surface=None,
            )

        try:
            system_lock_posture = self.get_system_lock_gate_posture()
        except Exception as exc:
            return _unavailable(
                review_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_lock_gate_posture() raised {type(exc).__name__}.",
                warnings=["REQUIRED_SURFACE_UNUSABLE", "SYSTEM_LOCK_SURFACE_CALL_FAILED"],
                cross_band_surface=cross_band_summary,
                system_lock_surface=None,
                observability_stage_surface=None,
                observability_quality_surface=None,
                observability_review_surface=None,
            )

        warnings: list[str] = []

        obs_stage_api = getattr(self, "get_observability_stage_lock_audit", None)
        if callable(obs_stage_api):
            try:
                observability_stage_lock = obs_stage_api()
            except Exception as exc:
                warnings.append("OBSERVABILITY_STAGE_LOCK_SURFACE_CALL_FAILED")
                warnings.append(f"OBSERVABILITY_STAGE_LOCK_EXCEPTION:{type(exc).__name__}")
        else:
            warnings.append("OBSERVABILITY_STAGE_LOCK_SURFACE_MISSING")

        obs_quality_api = getattr(self, "get_pressure_capture_quality_summary", None)
        if callable(obs_quality_api):
            try:
                observability_quality_summary = obs_quality_api()
            except Exception as exc:
                warnings.append("OBSERVABILITY_QUALITY_SURFACE_CALL_FAILED")
                warnings.append(f"OBSERVABILITY_QUALITY_EXCEPTION:{type(exc).__name__}")
        else:
            warnings.append("OBSERVABILITY_QUALITY_SURFACE_MISSING")

        obs_review_api_name = "get_observability_evidence_review_summary"
        obs_review_api = getattr(self, obs_review_api_name, None)
        if callable(obs_review_api):
            try:
                observability_review_summary = obs_review_api()
            except Exception as exc:
                warnings.append("OBSERVABILITY_EVIDENCE_REVIEW_SURFACE_CALL_FAILED")
                warnings.append(f"OBSERVABILITY_EVIDENCE_REVIEW_EXCEPTION:{type(exc).__name__}")
        else:
            warnings.append("OBSERVABILITY_EVIDENCE_REVIEW_SURFACE_MISSING")

        cross_scope = (
            cross_band_summary.get("evidence_scope", {})
            if isinstance(cross_band_summary, dict)
            else {}
        )
        cross_counts = (
            cross_band_summary.get("evidence_counts", {})
            if isinstance(cross_band_summary, dict)
            else {}
        )
        cross_review_state = (
            str(cross_band_summary.get("review_state", "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"))
            if isinstance(cross_band_summary, dict)
            else "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"
        )
        cross_stage_lock_state = str(
            cross_scope.get("stage_lock_state", "CROSS_BAND_STAGE_LOCK_UNAVAILABLE")
        )
        cross_auditable = _as_int(cross_scope.get("total_auditable_events", 0))

        gate_state = (
            str(system_lock_posture.get("gate_state", "SYSTEM_GATE_UNAVAILABLE"))
            if isinstance(system_lock_posture, dict)
            else "SYSTEM_GATE_UNAVAILABLE"
        )
        obs_stage_lock_state = (
            str(observability_stage_lock.get("lock_state", "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"))
            if isinstance(observability_stage_lock, dict)
            else "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"
        )

        # Observability capture quality remains reporting/context only.
        obs_quality_auditable = _as_int(
            observability_quality_summary.get("auditable_event_count", 0)
            if isinstance(observability_quality_summary, dict)
            else 0
        )
        obs_audit_state_counts = (
            observability_quality_summary.get("audit_state_counts", {})
            if isinstance(observability_quality_summary, dict)
            else {}
        )
        obs_recoverability_counts = (
            observability_quality_summary.get("recoverability_counts", {})
            if isinstance(observability_quality_summary, dict)
            else {}
        )

        obs_review_available = bool(
            isinstance(observability_review_summary, dict)
            and observability_review_summary.get("review_available", False)
        )
        obs_review_state = (
            str(
                observability_review_summary.get(
                    "review_state",
                    "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE",
                )
            )
            if isinstance(observability_review_summary, dict)
            else "OBSERVABILITY_EVIDENCE_REVIEW_UNAVAILABLE"
        )
        obs_review_scope = (
            observability_review_summary.get("evidence_scope", {})
            if isinstance(observability_review_summary, dict)
            else {}
        )
        obs_review_counts = (
            observability_review_summary.get("evidence_counts", {})
            if isinstance(observability_review_summary, dict)
            else {}
        )
        obs_review_auditable = _as_int(
            obs_review_scope.get(
                "total_auditable_events",
                obs_review_counts.get("total_auditable_events", 0)
                if isinstance(obs_review_counts, dict)
                else 0,
            )
            if isinstance(obs_review_scope, dict)
            else 0
        )

        total_auditable = cross_auditable + obs_review_auditable
        meaningful_surface_exists = total_auditable > 0

        # READY requires real cross-band + observability evidence-review surfaces.
        # Stage lock, gate posture, and capture quality remain contextual only.
        obs_review_ready = (
            obs_review_available
            and isinstance(obs_review_state, str)
            and obs_review_state.endswith("_READY")
        )
        ready = (
            cross_review_state == "CROSS_BAND_EVIDENCE_REVIEW_READY"
            and cross_auditable > 0
            and obs_review_ready
        )

        if ready:
            review_state = "SYSTEM_EVIDENCE_REVIEW_READY"
            review_reason = "COMPOSED_EVIDENCE_SURFACES_READY"
        elif not meaningful_surface_exists:
            review_state = "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
            review_reason = "NO_MEANINGFUL_EVIDENCE_SURFACE"
        else:
            review_state = "SYSTEM_EVIDENCE_REVIEW_PARTIAL"
            review_reason = "LIMITED_OR_ASYMMETRIC_EVIDENCE_SURFACE"

        supporting_surfaces = {
            "cross_band_evidence_review_summary": cross_band_summary,
            "observability_stage_lock_audit": observability_stage_lock,
            "observability_pressure_capture_quality_summary": observability_quality_summary,
            "observability_evidence_review_summary": observability_review_summary,
            "system_lock_gate_posture": system_lock_posture,
        }

        evidence_scope = {
            "cross_band_review_state": cross_review_state,
            "cross_band_stage_lock_state": cross_stage_lock_state,
            "observability_stage_lock_state": obs_stage_lock_state,
            "observability_review_state": obs_review_state,
            "system_gate_state": gate_state,
            "observability_review_surface_present": isinstance(observability_review_summary, dict),
            "coverage_notes": (
                list(cross_scope.get("coverage_notes", []))
                + list(observability_quality_summary.get("explanation_lines", []) if isinstance(observability_quality_summary, dict) else [])
            ),
        }

        evidence_counts = {
            "cross_band_total_auditable_events": cross_auditable,
            "observability_total_auditable_events": obs_review_auditable,
            "total_auditable_events": total_auditable,
            "cross_band_self_check_state_counts": (
                cross_counts
                if isinstance(cross_counts, dict)
                else {
                    "CROSS_BAND_ALIGNMENT_OBSERVED": 0,
                    "CROSS_BAND_CONTRADICTION_OBSERVED": 0,
                    "CROSS_BAND_PARTIAL": 0,
                    "CROSS_BAND_UNAVAILABLE": 0,
                }
            ),
            "observability_audit_state_counts": (
                obs_audit_state_counts
                if isinstance(obs_audit_state_counts, dict)
                else {
                    "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                    "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                }
            ),
            "observability_recoverability_counts": (
                obs_recoverability_counts
                if isinstance(obs_recoverability_counts, dict)
                else {
                    "FULLY_RECOVERABLE": 0,
                    "PARTIALLY_RECOVERABLE": 0,
                    "UNRECOVERABLE": 0,
                }
            ),
        }

        explanation_lines = [
            f"Review state: {review_state}",
            f"Review reason: {review_reason}",
            f"System gate posture: {gate_state}",
            f"Cross-band review state: {cross_review_state}",
            f"Observability evidence-review state: {obs_review_state}",
            f"Observability stage lock: {obs_stage_lock_state}",
            f"Total auditable events: {total_auditable}",
        ]
        if "OBSERVABILITY_EVIDENCE_REVIEW_SURFACE_MISSING" in warnings:
            explanation_lines.append(
                "Observability dedicated evidence-review API is absent; system evidence review remains non-ready."
            )
        if total_auditable == 0:
            explanation_lines.append("Evidence surface is thin (0 auditable events).")

        composed_warnings = []
        if isinstance(cross_band_summary, dict):
            composed_warnings.extend(cross_band_summary.get("warnings", []))
        if isinstance(system_lock_posture, dict):
            composed_warnings.extend(system_lock_posture.get("warnings", []))
        if isinstance(observability_stage_lock, dict):
            composed_warnings.extend(observability_stage_lock.get("warnings", []))
        if isinstance(observability_quality_summary, dict):
            composed_warnings.extend(observability_quality_summary.get("warnings", []))
        if isinstance(observability_review_summary, dict):
            composed_warnings.extend(observability_review_summary.get("warnings", []))
        composed_warnings.extend(warnings)

        return {
            "review_available": True,
            "review_mode": "SYSTEM_EVIDENCE_REVIEW",
            "review_state": review_state,
            "review_reason": review_reason,
            "system_lock_posture": system_lock_posture,
            "supporting_surfaces": supporting_surfaces,
            "evidence_scope": evidence_scope,
            "evidence_counts": evidence_counts,
            "warnings": sorted(set(composed_warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_evidence_review_stage_lock_audit(self) -> dict:
        """
        System Evidence Review Consistency / Stage Lock v1.2.
        Read-only freeze/audit layer over corrected system evidence-review posture.
        """
        _GUARDRAIL_FIELDS = [
            "lineage_mutation_performed",
            "event_creation_performed",
            "history_rewrite_performed",
        ]
        _SYS_API = "get_system_evidence_review_summary"
        _CB_API = "get_cross_band_evidence_review_summary"
        _GATE_API = "get_system_lock_gate_posture"
        _OBS_REVIEW_API = "get_observability_evidence_review_summary"
        _OBS_STAGE_API = "get_observability_stage_lock_audit"
        _OBS_QUALITY_API = "get_pressure_capture_quality_summary"

        _SYSTEM_STATES = {
            "SYSTEM_EVIDENCE_REVIEW_READY",
            "SYSTEM_EVIDENCE_REVIEW_PARTIAL",
            "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
        }

        def _check_pass(name: str, reason: str, details: Optional[dict] = None) -> dict:
            return {
                "check_name": name,
                "passed": True,
                "reason": reason,
                "details": details if isinstance(details, dict) else {},
            }

        def _check_fail(name: str, reason: str, details: Optional[dict] = None) -> dict:
            return {
                "check_name": name,
                "passed": False,
                "reason": reason,
                "details": details if isinstance(details, dict) else {},
            }

        def _safe_int(v) -> int:
            if isinstance(v, bool):
                return int(v)
            if isinstance(v, (int, float)):
                return int(v)
            return 0

        def _unavailable(
            *,
            reason: str,
            explanation: str,
            system_summary,
            cross_summary,
            gate_context,
        ) -> dict:
            return {
                "audit_available": False,
                "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE",
                "reason": reason,
                "supporting_surfaces": {
                    "system_evidence_review_summary": system_summary,
                    "cross_band_evidence_review_summary": cross_summary,
                    "system_lock_gate_posture": gate_context,
                },
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": {
                    "required_surfaces": {
                        "system_evidence_review_api_present": callable(getattr(self, _SYS_API, None)),
                        "cross_band_evidence_review_api_present": callable(getattr(self, _CB_API, None)),
                        "system_lock_gate_posture_api_present": callable(getattr(self, _GATE_API, None)),
                    },
                    "optional_surfaces": {
                        "observability_evidence_review_api_present": callable(getattr(self, _OBS_REVIEW_API, None)),
                        "observability_stage_lock_api_present": callable(getattr(self, _OBS_STAGE_API, None)),
                        "observability_quality_api_present": callable(getattr(self, _OBS_QUALITY_API, None)),
                    },
                    "ready_predicate_contract": {
                        "requires_cross_band_ready": True,
                        "requires_cross_band_auditable_gt_zero": True,
                        "requires_observability_evidence_review_ready": True,
                        "disallows_system_gate_as_ready_predicate": True,
                        "disallows_observability_stage_lock_as_ready_substitute": True,
                        "disallows_observability_quality_as_ready_substitute": True,
                    },
                },
                "warnings": [],
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        required_missing = [
            _SYS_API for _ in [0] if not callable(getattr(self, _SYS_API, None))
        ]
        if not callable(getattr(self, _CB_API, None)):
            required_missing.append(_CB_API)
        if not callable(getattr(self, _GATE_API, None)):
            required_missing.append(_GATE_API)
        if required_missing:
            return _unavailable(
                reason="REQUIRED_SURFACE_MISSING",
                explanation="Required stage-lock surface missing: " + ", ".join(required_missing) + ".",
                system_summary=None,
                cross_summary=None,
                gate_context=None,
            )

        try:
            system_summary = self.get_system_evidence_review_summary()
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_evidence_review_summary() raised {type(exc).__name__}.",
                system_summary=None,
                cross_summary=None,
                gate_context=None,
            )
        try:
            cross_summary = self.get_cross_band_evidence_review_summary()
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_cross_band_evidence_review_summary() raised {type(exc).__name__}.",
                system_summary=system_summary,
                cross_summary=None,
                gate_context=None,
            )
        try:
            gate_context = self.get_system_lock_gate_posture()
        except Exception as exc:
            return _unavailable(
                reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_lock_gate_posture() raised {type(exc).__name__}.",
                system_summary=system_summary,
                cross_summary=cross_summary,
                gate_context=None,
            )

        check_results: list[dict] = []
        warnings: list[str] = []

        system_shape_ok = (
            isinstance(system_summary, dict)
            and system_summary.get("review_mode") == "SYSTEM_EVIDENCE_REVIEW"
            and system_summary.get("review_state") in _SYSTEM_STATES
        )
        if system_shape_ok:
            check_results.append(
                _check_pass(
                    "SYSTEM_EVIDENCE_REVIEW_SURFACE_USABLE",
                    "SYSTEM_SUMMARY_SHAPE_OK",
                    {
                        "review_state": system_summary.get("review_state"),
                        "review_reason": system_summary.get("review_reason"),
                    },
                )
            )
        else:
            check_results.append(
                _check_fail(
                    "SYSTEM_EVIDENCE_REVIEW_SURFACE_USABLE",
                    "SYSTEM_SUMMARY_SHAPE_UNEXPECTED",
                    {"system_summary_type": type(system_summary).__name__},
                )
            )

        cross_shape_ok = (
            isinstance(cross_summary, dict)
            and cross_summary.get("review_mode") == "CROSS_BAND_EVIDENCE_REVIEW"
            and isinstance(cross_summary.get("review_state"), str)
        )
        if cross_shape_ok:
            check_results.append(
                _check_pass(
                    "CROSS_BAND_ANCHOR_SURFACE_USABLE",
                    "CROSS_BAND_SUMMARY_SHAPE_OK",
                    {"review_state": cross_summary.get("review_state")},
                )
            )
        else:
            check_results.append(
                _check_fail(
                    "CROSS_BAND_ANCHOR_SURFACE_USABLE",
                    "CROSS_BAND_SUMMARY_SHAPE_UNEXPECTED",
                    {"cross_summary_type": type(cross_summary).__name__},
                )
            )

        gate_shape_ok = (
            isinstance(gate_context, dict)
            and gate_context.get("gate_mode") == "SYSTEM_LOCK_GATE_POSTURE"
            and isinstance(gate_context.get("gate_state"), str)
        )
        if gate_shape_ok:
            check_results.append(
                _check_pass(
                    "SYSTEM_LOCK_CONTEXT_SURFACE_USABLE",
                    "SYSTEM_GATE_SHAPE_OK",
                    {"gate_state": gate_context.get("gate_state")},
                )
            )
        else:
            check_results.append(
                _check_fail(
                    "SYSTEM_LOCK_CONTEXT_SURFACE_USABLE",
                    "SYSTEM_GATE_SHAPE_UNEXPECTED",
                    {"gate_context_type": type(gate_context).__name__},
                )
            )

        if not (system_shape_ok and cross_shape_ok and gate_shape_ok):
            failed_shape = [c["check_name"] for c in check_results if c.get("passed") is False]
            return {
                "audit_available": False,
                "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
                "lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE",
                "reason": "REQUIRED_SURFACE_SHAPE_INVALID",
                "supporting_surfaces": {
                    "system_evidence_review_summary": system_summary,
                    "cross_band_evidence_review_summary": cross_summary,
                    "system_lock_gate_posture": gate_context,
                },
                "checks_run": len(check_results),
                "checks_passed": sum(1 for c in check_results if c.get("passed") is True),
                "checks_failed": sum(1 for c in check_results if c.get("passed") is False),
                "check_results": check_results,
                "contract_surface": {
                    "required_surfaces": {
                        "system_evidence_review_api_present": True,
                        "cross_band_evidence_review_api_present": True,
                        "system_lock_gate_posture_api_present": True,
                    },
                    "optional_surfaces": {
                        "observability_evidence_review_api_present": callable(getattr(self, _OBS_REVIEW_API, None)),
                        "observability_stage_lock_api_present": callable(getattr(self, _OBS_STAGE_API, None)),
                        "observability_quality_api_present": callable(getattr(self, _OBS_QUALITY_API, None)),
                    },
                    "ready_predicate_contract": {
                        "requires_cross_band_ready": True,
                        "requires_cross_band_auditable_gt_zero": True,
                        "requires_observability_evidence_review_ready": True,
                        "disallows_system_gate_as_ready_predicate": True,
                        "disallows_observability_stage_lock_as_ready_substitute": True,
                        "disallows_observability_quality_as_ready_substitute": True,
                    },
                },
                "warnings": [],
                "explanation_lines": [
                    "Required surface shape invalid; failed: " + ", ".join(failed_shape)
                ],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        system_state = str(system_summary.get("review_state"))
        supporting = system_summary.get("supporting_surfaces", {})
        if not isinstance(supporting, dict):
            supporting = {}
        obs_review_surface = supporting.get("observability_evidence_review_summary")
        obs_review_ready = (
            isinstance(obs_review_surface, dict)
            and bool(obs_review_surface.get("review_available", False))
            and isinstance(obs_review_surface.get("review_state"), str)
            and str(obs_review_surface.get("review_state")).endswith("_READY")
        )

        if system_state == "SYSTEM_EVIDENCE_REVIEW_READY":
            if obs_review_ready:
                check_results.append(
                    _check_pass(
                        "READY_REQUIRES_OBSERVABILITY_EVIDENCE_REVIEW",
                        "OBSERVABILITY_REVIEW_READY_PRESENT",
                        {"observability_review_state": obs_review_surface.get("review_state")},
                    )
                )
            else:
                check_results.append(
                    _check_fail(
                        "READY_REQUIRES_OBSERVABILITY_EVIDENCE_REVIEW",
                        "SYSTEM_READY_WITHOUT_OBSERVABILITY_REVIEW_READY",
                        {"observability_review_surface_present": isinstance(obs_review_surface, dict)},
                    )
                )
        else:
            check_results.append(
                _check_pass(
                    "READY_REQUIRES_OBSERVABILITY_EVIDENCE_REVIEW",
                    "SYSTEM_NOT_READY_NOT_APPLICABLE",
                    {"system_review_state": system_state},
                )
            )

        cross_state = str(cross_summary.get("review_state", "CROSS_BAND_EVIDENCE_REVIEW_UNAVAILABLE"))
        cross_scope = cross_summary.get("evidence_scope", {})
        if not isinstance(cross_scope, dict):
            cross_scope = {}
        cross_auditable = _safe_int(cross_scope.get("total_auditable_events", 0))
        cross_ready_with_evidence = (
            cross_state == "CROSS_BAND_EVIDENCE_REVIEW_READY"
            and cross_auditable > 0
        )
        if cross_ready_with_evidence and not obs_review_ready:
            if system_state != "SYSTEM_EVIDENCE_REVIEW_READY":
                check_results.append(
                    _check_pass(
                        "NO_FAKE_SYMMETRY_WHEN_OBSERVABILITY_REVIEW_MISSING",
                        "SYSTEM_NOT_READY_UNDER_ASYMMETRY",
                        {
                            "system_review_state": system_state,
                            "cross_band_review_state": cross_state,
                        },
                    )
                )
            else:
                check_results.append(
                    _check_fail(
                        "NO_FAKE_SYMMETRY_WHEN_OBSERVABILITY_REVIEW_MISSING",
                        "SYSTEM_READY_UNDER_ASYMMETRY",
                        {
                            "system_review_state": system_state,
                            "cross_band_review_state": cross_state,
                        },
                    )
                )
        else:
            check_results.append(
                _check_pass(
                    "NO_FAKE_SYMMETRY_WHEN_OBSERVABILITY_REVIEW_MISSING",
                    "ASYMMETRY_NOT_TRIGGERED",
                    {
                        "cross_band_ready_with_evidence": cross_ready_with_evidence,
                        "observability_review_ready": obs_review_ready,
                    },
                )
            )

        # System-gate context must not control top-level evidence review classification.
        gate_non_predicate_ok = True
        gate_details = {"base_state": system_state, "base_reason": system_summary.get("review_reason")}
        original_gate_api = getattr(self, _GATE_API, None)
        try:
            if callable(original_gate_api):
                def _patched_gate():
                    out = original_gate_api()
                    if not isinstance(out, dict):
                        return {
                            "gate_available": True,
                            "gate_mode": "SYSTEM_LOCK_GATE_POSTURE",
                            "gate_state": "SYSTEM_GATE_UNAVAILABLE",
                            "gate_reason": "STAGE_LOCK_PATCHED_GATE",
                            "warnings": [],
                        }
                    patched = dict(out)
                    current = str(patched.get("gate_state", "SYSTEM_GATE_UNAVAILABLE"))
                    patched["gate_state"] = (
                        "SYSTEM_GATE_UNAVAILABLE"
                        if current == "SYSTEM_GATE_LOCKED"
                        else "SYSTEM_GATE_LOCKED"
                    )
                    return patched

                setattr(self, _GATE_API, _patched_gate)
                gate_perturbed = self.get_system_evidence_review_summary()
                gate_details["perturbed_state"] = gate_perturbed.get("review_state")
                gate_details["perturbed_reason"] = gate_perturbed.get("review_reason")
                if (
                    gate_perturbed.get("review_state") != system_summary.get("review_state")
                    or gate_perturbed.get("review_reason") != system_summary.get("review_reason")
                ):
                    gate_non_predicate_ok = False
        except Exception as exc:
            gate_non_predicate_ok = False
            gate_details["exception"] = type(exc).__name__
        finally:
            if callable(original_gate_api):
                setattr(self, _GATE_API, original_gate_api)

        if gate_non_predicate_ok:
            check_results.append(
                _check_pass(
                    "SYSTEM_GATE_CONTEXT_NON_PREDICATE",
                    "SYSTEM_GATE_DOES_NOT_CHANGE_SYSTEM_REVIEW_CLASSIFICATION",
                    gate_details,
                )
            )
        else:
            check_results.append(
                _check_fail(
                    "SYSTEM_GATE_CONTEXT_NON_PREDICATE",
                    "SYSTEM_GATE_CHANGES_SYSTEM_REVIEW_CLASSIFICATION",
                    gate_details,
                )
            )

        # Observability stage lock must remain contextual; it cannot substitute for observability review.
        stage_non_substitute_ok = True
        stage_details = {"base_state": system_state, "base_reason": system_summary.get("review_reason")}
        original_obs_stage_api = getattr(self, _OBS_STAGE_API, None)
        try:
            if callable(original_obs_stage_api):
                def _patched_obs_stage():
                    out = original_obs_stage_api()
                    if not isinstance(out, dict):
                        return {
                            "audit_available": True,
                            "audit_mode": "OBSERVABILITY_STAGE_LOCK",
                            "lock_state": "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE",
                            "reason": "STAGE_LOCK_PATCHED_OBS",
                            "warnings": [],
                        }
                    patched = dict(out)
                    current = str(patched.get("lock_state", "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"))
                    patched["lock_state"] = (
                        "OBSERVABILITY_STAGE_LOCK_UNAVAILABLE"
                        if current == "OBSERVABILITY_STAGE_LOCKED"
                        else "OBSERVABILITY_STAGE_LOCKED"
                    )
                    return patched

                setattr(self, _OBS_STAGE_API, _patched_obs_stage)
                stage_perturbed = self.get_system_evidence_review_summary()
                stage_details["perturbed_state"] = stage_perturbed.get("review_state")
                stage_details["perturbed_reason"] = stage_perturbed.get("review_reason")
                if (
                    stage_perturbed.get("review_state") != system_summary.get("review_state")
                    or stage_perturbed.get("review_reason") != system_summary.get("review_reason")
                ):
                    stage_non_substitute_ok = False
            else:
                stage_details["not_applicable"] = "OBSERVABILITY_STAGE_LOCK_SURFACE_MISSING"
        except Exception as exc:
            stage_non_substitute_ok = False
            stage_details["exception"] = type(exc).__name__
        finally:
            if callable(original_obs_stage_api):
                setattr(self, _OBS_STAGE_API, original_obs_stage_api)

        if stage_non_substitute_ok:
            check_results.append(
                _check_pass(
                    "OBSERVABILITY_STAGE_LOCK_CONTEXT_NON_SUBSTITUTE",
                    "OBS_STAGE_LOCK_DOES_NOT_CHANGE_SYSTEM_REVIEW_CLASSIFICATION",
                    stage_details,
                )
            )
        else:
            check_results.append(
                _check_fail(
                    "OBSERVABILITY_STAGE_LOCK_CONTEXT_NON_SUBSTITUTE",
                    "OBS_STAGE_LOCK_CHANGES_SYSTEM_REVIEW_CLASSIFICATION",
                    stage_details,
                )
            )

        # Observability quality must remain contextual; it cannot control top-level classification.
        quality_non_substitute_ok = True
        quality_details = {"base_state": system_state, "base_reason": system_summary.get("review_reason")}
        original_quality_api = getattr(self, _OBS_QUALITY_API, None)
        try:
            if callable(original_quality_api):
                def _patched_quality():
                    out = original_quality_api()
                    if not isinstance(out, dict):
                        return {
                            "summary_available": False,
                            "auditable_event_count": 0,
                            "audit_state_counts": {
                                "PRESSURE_CAPTURE_AUDIT_VALID": 0,
                                "PRESSURE_CAPTURE_AUDIT_INVALID": 0,
                                "PRESSURE_CAPTURE_AUDIT_UNAVAILABLE": 0,
                            },
                            "recoverability_counts": {
                                "FULLY_RECOVERABLE": 0,
                                "PARTIALLY_RECOVERABLE": 0,
                                "UNRECOVERABLE": 0,
                            },
                            "warnings": [],
                        }
                    patched = dict(out)
                    patched["summary_available"] = not bool(patched.get("summary_available", False))
                    base_count = _safe_int(patched.get("auditable_event_count", 0))
                    patched["auditable_event_count"] = 0 if base_count > 0 else 999
                    return patched

                setattr(self, _OBS_QUALITY_API, _patched_quality)
                quality_perturbed = self.get_system_evidence_review_summary()
                quality_details["perturbed_state"] = quality_perturbed.get("review_state")
                quality_details["perturbed_reason"] = quality_perturbed.get("review_reason")
                if (
                    quality_perturbed.get("review_state") != system_summary.get("review_state")
                    or quality_perturbed.get("review_reason") != system_summary.get("review_reason")
                ):
                    quality_non_substitute_ok = False
            else:
                quality_details["not_applicable"] = "OBSERVABILITY_QUALITY_SURFACE_MISSING"
        except Exception as exc:
            quality_non_substitute_ok = False
            quality_details["exception"] = type(exc).__name__
        finally:
            if callable(original_quality_api):
                setattr(self, _OBS_QUALITY_API, original_quality_api)

        if quality_non_substitute_ok:
            check_results.append(
                _check_pass(
                    "OBSERVABILITY_QUALITY_CONTEXT_NON_SUBSTITUTE",
                    "OBS_QUALITY_DOES_NOT_CHANGE_SYSTEM_REVIEW_CLASSIFICATION",
                    quality_details,
                )
            )
        else:
            check_results.append(
                _check_fail(
                    "OBSERVABILITY_QUALITY_CONTEXT_NON_SUBSTITUTE",
                    "OBS_QUALITY_CHANGES_SYSTEM_REVIEW_CLASSIFICATION",
                    quality_details,
                )
            )

        guard_violations = []
        for name, payload in [
            ("system_evidence_review_summary", system_summary),
            ("cross_band_evidence_review_summary", cross_summary),
            ("system_lock_gate_posture", gate_context),
        ]:
            for field in _GUARDRAIL_FIELDS:
                if payload.get(field) is not False:
                    guard_violations.append(f"{name}.{field}")
        if not guard_violations:
            check_results.append(
                _check_pass(
                    "READ_ONLY_GUARDRAILS_FALSE",
                    "ALL_GUARDRAIL_FLAGS_FALSE",
                    {"checked_fields": list(_GUARDRAIL_FIELDS)},
                )
            )
        else:
            check_results.append(
                _check_fail(
                    "READ_ONLY_GUARDRAILS_FALSE",
                    "GUARDRAIL_FLAG_VIOLATION",
                    {"violations": guard_violations},
                )
            )
            warnings.append("GUARDRAIL_FLAG_VIOLATION")

        checks_run = len(check_results)
        checks_passed = sum(1 for c in check_results if c.get("passed") is True)
        checks_failed = checks_run - checks_passed

        if checks_failed == 0:
            lock_state = "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED"
            reason = "ALL_CONSISTENCY_CHECKS_PASSED"
            explanation_lines = [
                "System evidence-review stage-lock checks passed.",
            ]
        else:
            lock_state = "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
            reason = "CONSISTENCY_CHECK_FAILED"
            failed_checks = [c["check_name"] for c in check_results if c.get("passed") is False]
            explanation_lines = [
                "System evidence-review stage-lock inconsistency detected.",
                "Failed checks: " + ", ".join(failed_checks),
            ]

        surface_warnings = []
        for payload in [system_summary, cross_summary, gate_context]:
            if isinstance(payload, dict):
                surface_warnings.extend(payload.get("warnings", []))
        surface_warnings.extend(warnings)

        return {
            "audit_available": True,
            "audit_mode": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK",
            "lock_state": lock_state,
            "reason": reason,
            "supporting_surfaces": {
                "system_evidence_review_summary": system_summary,
                "cross_band_evidence_review_summary": cross_summary,
                "system_lock_gate_posture": gate_context,
            },
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "check_results": check_results,
            "contract_surface": {
                "required_surfaces": {
                    "system_evidence_review_api_present": True,
                    "cross_band_evidence_review_api_present": True,
                    "system_lock_gate_posture_api_present": True,
                },
                "optional_surfaces": {
                    "observability_evidence_review_api_present": callable(getattr(self, _OBS_REVIEW_API, None)),
                    "observability_stage_lock_api_present": callable(getattr(self, _OBS_STAGE_API, None)),
                    "observability_quality_api_present": callable(getattr(self, _OBS_QUALITY_API, None)),
                },
                "ready_predicate_contract": {
                    "requires_cross_band_ready": True,
                    "requires_cross_band_auditable_gt_zero": True,
                    "requires_observability_evidence_review_ready": True,
                    "disallows_system_gate_as_ready_predicate": True,
                    "disallows_observability_stage_lock_as_ready_substitute": True,
                    "disallows_observability_quality_as_ready_substitute": True,
                },
            },
            "warnings": sorted(set(surface_warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_evidence_review_consumer_gate(self) -> dict:
        """
        System Evidence Review Consumer Gate v1.3.
        Strictly read-only consumer gate over system evidence-review posture.
        """
        summary = self.get_system_evidence_review_summary()
        stage_lock = self.get_system_evidence_review_stage_lock_audit()

        summary_available = bool(
            isinstance(summary, dict) and summary.get("review_available", False)
        )
        review_state = (
            str(summary.get("review_state", "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"))
            if isinstance(summary, dict)
            else "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
        )

        audit_available = bool(
            isinstance(stage_lock, dict) and stage_lock.get("audit_available", False)
        )
        lock_state = (
            str(stage_lock.get("lock_state", "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"))
            if isinstance(stage_lock, dict)
            else "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"
        )

        if not audit_available:
            gate_state = "SYSTEM_EVIDENCE_GATE_HOLD"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_AUDIT_UNAVAILABLE"
        elif lock_state == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT":
            gate_state = "SYSTEM_EVIDENCE_GATE_HOLD"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_INCONSISTENT"
        elif lock_state == "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE":
            gate_state = "SYSTEM_EVIDENCE_GATE_HOLD"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"
        elif lock_state != "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCKED":
            gate_state = "SYSTEM_EVIDENCE_GATE_HOLD"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNUSABLE"
        elif not summary_available:
            gate_state = "SYSTEM_EVIDENCE_GATE_HOLD"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
        elif review_state == "SYSTEM_EVIDENCE_REVIEW_READY":
            gate_state = "SYSTEM_EVIDENCE_GATE_RELY"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_READY_AND_STAGE_LOCKED"
        elif review_state == "SYSTEM_EVIDENCE_REVIEW_PARTIAL":
            gate_state = "SYSTEM_EVIDENCE_GATE_LIMITED"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_PARTIAL_UNDER_STAGE_LOCK"
        elif review_state == "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE":
            gate_state = "SYSTEM_EVIDENCE_GATE_HOLD"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
        else:
            gate_state = "SYSTEM_EVIDENCE_GATE_HOLD"
            gate_reason = "SYSTEM_EVIDENCE_REVIEW_STATE_UNUSABLE"

        explanation_lines = [
            f"Consumer gate state: {gate_state}",
            f"Consumer gate reason: {gate_reason}",
            f"System evidence review state: {review_state}",
            f"System evidence review stage lock: {lock_state}",
        ]
        if isinstance(summary, dict) and isinstance(summary.get("explanation_lines"), list):
            explanation_lines.extend(summary.get("explanation_lines", []))
        if isinstance(stage_lock, dict) and isinstance(stage_lock.get("explanation_lines"), list):
            explanation_lines.extend(stage_lock.get("explanation_lines", []))

        warnings = []
        if isinstance(summary, dict):
            warnings.extend(summary.get("warnings", []))
        if isinstance(stage_lock, dict):
            warnings.extend(stage_lock.get("warnings", []))

        return {
            "gate_available": True,
            "gate_mode": "SYSTEM_EVIDENCE_REVIEW_CONSUMER_GATE",
            "gate_state": gate_state,
            "gate_reason": gate_reason,
            "system_evidence_review": summary,
            "system_evidence_review_stage_lock": stage_lock,
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_system_evidence_consumer_summary(self) -> dict:
        """
        System Evidence Consumer Summary v1.4.
        Read-only packaging/reporting surface over v1.1/v1.2/v1.3 outputs.
        """
        _SUMMARY_API = "get_system_evidence_review_summary"
        _STAGE_LOCK_API = "get_system_evidence_review_stage_lock_audit"
        _GATE_API = "get_system_evidence_review_consumer_gate"

        def _unavailable(
            *,
            summary_reason: str,
            explanation: str,
            summary_surface,
            stage_lock_surface,
            gate_surface,
            warnings: list[str],
        ) -> dict:
            return {
                "summary_available": False,
                "summary_mode": "SYSTEM_EVIDENCE_CONSUMER_SUMMARY",
                "summary_state": "SYSTEM_EVIDENCE_SUMMARY_UNAVAILABLE",
                "summary_reason": summary_reason,
                "consumer_posture": {
                    "review_state": "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
                    "stage_lock_state": "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE",
                    "gate_state": "SYSTEM_EVIDENCE_GATE_HOLD",
                    "gate_reason": "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE",
                },
                "supporting_surfaces": {
                    "system_evidence_review_summary": summary_surface,
                    "system_evidence_review_stage_lock": stage_lock_surface,
                    "system_evidence_review_consumer_gate": gate_surface,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        required_missing = []
        if not callable(getattr(self, _SUMMARY_API, None)):
            required_missing.append(_SUMMARY_API)
        if not callable(getattr(self, _STAGE_LOCK_API, None)):
            required_missing.append(_STAGE_LOCK_API)
        if not callable(getattr(self, _GATE_API, None)):
            required_missing.append(_GATE_API)
        if required_missing:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required consumer-summary surface missing: "
                    + ", ".join(required_missing)
                    + "."
                ),
                summary_surface=None,
                stage_lock_surface=None,
                gate_surface=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        summary_surface = None
        stage_lock_surface = None
        gate_surface = None

        try:
            summary_surface = self.get_system_evidence_review_summary()
        except Exception as exc:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_evidence_review_summary() raised {type(exc).__name__}.",
                summary_surface=None,
                stage_lock_surface=None,
                gate_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "SYSTEM_EVIDENCE_REVIEW_SUMMARY_CALL_FAILED"],
            )

        try:
            stage_lock_surface = self.get_system_evidence_review_stage_lock_audit()
        except Exception as exc:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_evidence_review_stage_lock_audit() raised {type(exc).__name__}.",
                summary_surface=summary_surface,
                stage_lock_surface=None,
                gate_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "SYSTEM_EVIDENCE_STAGE_LOCK_CALL_FAILED"],
            )

        try:
            gate_surface = self.get_system_evidence_review_consumer_gate()
        except Exception as exc:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_evidence_review_consumer_gate() raised {type(exc).__name__}.",
                summary_surface=summary_surface,
                stage_lock_surface=stage_lock_surface,
                gate_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "SYSTEM_EVIDENCE_CONSUMER_GATE_CALL_FAILED"],
            )

        review_state = (
            str(summary_surface.get("review_state", "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"))
            if isinstance(summary_surface, dict)
            else "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
        )
        stage_lock_state = (
            str(stage_lock_surface.get("lock_state", "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"))
            if isinstance(stage_lock_surface, dict)
            else "SYSTEM_EVIDENCE_REVIEW_STAGE_LOCK_UNAVAILABLE"
        )
        gate_state = (
            str(gate_surface.get("gate_state", "SYSTEM_EVIDENCE_GATE_HOLD"))
            if isinstance(gate_surface, dict)
            else "SYSTEM_EVIDENCE_GATE_HOLD"
        )
        gate_reason = (
            str(gate_surface.get("gate_reason", "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"))
            if isinstance(gate_surface, dict)
            else "SYSTEM_EVIDENCE_REVIEW_UNAVAILABLE"
        )

        warnings = []
        if isinstance(summary_surface, dict):
            warnings.extend(summary_surface.get("warnings", []))
        if isinstance(stage_lock_surface, dict):
            warnings.extend(stage_lock_surface.get("warnings", []))
        if isinstance(gate_surface, dict):
            warnings.extend(gate_surface.get("warnings", []))

        explanation_lines = [
            f"Summary state: {gate_state}",
            f"Summary reason: {gate_reason}",
            f"Review state: {review_state}",
            f"Stage lock state: {stage_lock_state}",
            f"Consumer gate state: {gate_state}",
        ]
        if isinstance(gate_surface, dict) and isinstance(gate_surface.get("explanation_lines"), list):
            explanation_lines.extend(gate_surface.get("explanation_lines", []))

        return {
            "summary_available": True,
            "summary_mode": "SYSTEM_EVIDENCE_CONSUMER_SUMMARY",
            "summary_state": gate_state,
            "summary_reason": gate_reason,
            "consumer_posture": {
                "review_state": review_state,
                "stage_lock_state": stage_lock_state,
                "gate_state": gate_state,
                "gate_reason": gate_reason,
            },
            "supporting_surfaces": {
                "system_evidence_review_summary": summary_surface,
                "system_evidence_review_stage_lock": stage_lock_surface,
                "system_evidence_review_consumer_gate": gate_surface,
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_unified_system_consumer_posture_summary(self) -> dict:
        """
        Unified System Consumer Posture Summary v1.0.
        Read-only top-level composition over system evidence consumer summary and system lock gate posture.
        """
        _EVIDENCE_API = "get_system_evidence_consumer_summary"
        _LOCK_API = "get_system_lock_gate_posture"

        def _unavailable(
            *,
            summary_reason: str,
            explanation: str,
            evidence_surface,
            lock_surface,
            warnings: list[str],
        ) -> dict:
            return {
                "summary_available": False,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
                "summary_state": "SYSTEM_CONSUMER_UNAVAILABLE",
                "summary_reason": summary_reason,
                "unified_consumer_posture": {
                    "posture_state": "SYSTEM_CONSUMER_UNAVAILABLE",
                    "evidence_consumer_state": "SYSTEM_EVIDENCE_SUMMARY_UNAVAILABLE",
                    "system_lock_gate_state": "SYSTEM_GATE_UNAVAILABLE",
                    "evidence_equivalence": "HOLD_EQUIVALENT",
                    "lock_equivalence": "HOLD_EQUIVALENT",
                },
                "supporting_surfaces": {
                    "system_evidence_consumer_summary": evidence_surface,
                    "system_lock_gate_posture": lock_surface,
                },
                "warnings": sorted(set(warnings)),
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        required_missing = []
        if not callable(getattr(self, _EVIDENCE_API, None)):
            required_missing.append(_EVIDENCE_API)
        if not callable(getattr(self, _LOCK_API, None)):
            required_missing.append(_LOCK_API)
        if required_missing:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required unified-consumer surface missing: "
                    + ", ".join(required_missing)
                    + "."
                ),
                evidence_surface=None,
                lock_surface=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        evidence_summary = None
        lock_gate = None
        try:
            evidence_summary = self.get_system_evidence_consumer_summary()
        except Exception as exc:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_evidence_consumer_summary() raised {type(exc).__name__}.",
                evidence_surface=None,
                lock_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "SYSTEM_EVIDENCE_CONSUMER_SUMMARY_CALL_FAILED"],
            )
        try:
            lock_gate = self.get_system_lock_gate_posture()
        except Exception as exc:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_system_lock_gate_posture() raised {type(exc).__name__}.",
                evidence_surface=evidence_summary,
                lock_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "SYSTEM_LOCK_GATE_POSTURE_CALL_FAILED"],
            )

        evidence_shape_ok = (
            isinstance(evidence_summary, dict)
            and isinstance(evidence_summary.get("summary_state"), str)
        )
        lock_shape_ok = (
            isinstance(lock_gate, dict)
            and isinstance(lock_gate.get("gate_state"), str)
        )
        if not evidence_shape_ok or not lock_shape_ok:
            bad = []
            if not evidence_shape_ok:
                bad.append("SYSTEM_EVIDENCE_CONSUMER_SUMMARY_SHAPE_INVALID")
            if not lock_shape_ok:
                bad.append("SYSTEM_LOCK_GATE_POSTURE_SHAPE_INVALID")
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Required unified-consumer surface shape invalid: " + ", ".join(bad) + ".",
                evidence_surface=evidence_summary,
                lock_surface=lock_gate,
                warnings=bad,
            )

        evidence_available = bool(evidence_summary.get("summary_available", False))
        evidence_state = str(evidence_summary.get("summary_state", "SYSTEM_EVIDENCE_SUMMARY_UNAVAILABLE"))
        evidence_reason = str(evidence_summary.get("summary_reason", "SYSTEM_EVIDENCE_SUMMARY_REASON_MISSING"))

        lock_available = bool(lock_gate.get("gate_available", False))
        lock_state = str(lock_gate.get("gate_state", "SYSTEM_GATE_UNAVAILABLE"))
        lock_reason = str(lock_gate.get("gate_reason", "SYSTEM_LOCK_GATE_REASON_MISSING"))

        def _evidence_equivalence() -> str:
            if not evidence_available:
                return "HOLD_EQUIVALENT"
            if evidence_state == "SYSTEM_EVIDENCE_GATE_RELY":
                return "RELY_EQUIVALENT"
            if evidence_state == "SYSTEM_EVIDENCE_GATE_LIMITED":
                return "LIMITED_EQUIVALENT"
            if evidence_state in ("SYSTEM_EVIDENCE_GATE_HOLD", "SYSTEM_EVIDENCE_SUMMARY_UNAVAILABLE"):
                return "HOLD_EQUIVALENT"
            return "HOLD_EQUIVALENT"

        def _lock_equivalence() -> str:
            if not lock_available:
                return "HOLD_EQUIVALENT"
            if lock_state == "SYSTEM_GATE_LOCKED":
                return "RELY_EQUIVALENT"
            if lock_state in ("SYSTEM_GATE_LIMITED",):
                return "LIMITED_EQUIVALENT"
            if lock_state in ("SYSTEM_GATE_UNAVAILABLE", "SYSTEM_GATE_INCONSISTENT", "SYSTEM_GATE_HOLD"):
                return "HOLD_EQUIVALENT"
            return "HOLD_EQUIVALENT"

        evidence_equiv = _evidence_equivalence()
        lock_equiv = _lock_equivalence()

        if evidence_equiv == "RELY_EQUIVALENT" and lock_equiv == "RELY_EQUIVALENT":
            summary_state = "SYSTEM_CONSUMER_RELY"
            summary_reason = "BOTH_SIDES_RELY_EQUIVALENT"
        elif evidence_equiv == "HOLD_EQUIVALENT" or lock_equiv == "HOLD_EQUIVALENT":
            summary_state = "SYSTEM_CONSUMER_HOLD"
            summary_reason = "HOLD_EQUIVALENT_INPUT_POSTURE"
        elif evidence_equiv == "LIMITED_EQUIVALENT" or lock_equiv == "LIMITED_EQUIVALENT":
            summary_state = "SYSTEM_CONSUMER_LIMITED"
            summary_reason = "LIMITED_EQUIVALENT_INPUT_POSTURE"
        else:
            summary_state = "SYSTEM_CONSUMER_HOLD"
            summary_reason = "FAIL_CLOSED_CONSERVATIVE"

        warnings = []
        if isinstance(evidence_summary, dict):
            warnings.extend(evidence_summary.get("warnings", []))
        if isinstance(lock_gate, dict):
            warnings.extend(lock_gate.get("warnings", []))

        explanation_lines = [
            f"Unified posture state: {summary_state}",
            f"Unified posture reason: {summary_reason}",
            f"Evidence consumer state: {evidence_state}",
            f"System lock gate state: {lock_state}",
            f"Evidence equivalence: {evidence_equiv}",
            f"Lock equivalence: {lock_equiv}",
            f"Evidence reason: {evidence_reason}",
            f"Lock reason: {lock_reason}",
        ]

        return {
            "summary_available": True,
            "summary_mode": "UNIFIED_SYSTEM_CONSUMER_POSTURE",
            "summary_state": summary_state,
            "summary_reason": summary_reason,
            "unified_consumer_posture": {
                "posture_state": summary_state,
                "evidence_consumer_state": evidence_state,
                "system_lock_gate_state": lock_state,
                "evidence_equivalence": evidence_equiv,
                "lock_equivalence": lock_equiv,
            },
            "supporting_surfaces": {
                "system_evidence_consumer_summary": evidence_summary,
                "system_lock_gate_posture": lock_gate,
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_unified_system_consumer_posture_stage_lock_audit(self) -> dict:
        """
        Unified System Consumer Consistency / Stage Lock v1.1.
        Read-only freeze/audit layer over unified top consumer posture summary.
        """
        _UNIFIED_API = "get_unified_system_consumer_posture_summary"
        _GUARDRAILS = [
            "lineage_mutation_performed",
            "event_creation_performed",
            "history_rewrite_performed",
        ]
        _CANONICAL_STATES = {
            "SYSTEM_CONSUMER_RELY",
            "SYSTEM_CONSUMER_LIMITED",
            "SYSTEM_CONSUMER_HOLD",
            "SYSTEM_CONSUMER_UNAVAILABLE",
        }

        def _check(check_name: str, passed: bool, reason: str, details: Optional[dict] = None) -> dict:
            return {
                "check_name": check_name,
                "passed": bool(passed),
                "reason": reason,
                "details": details if isinstance(details, dict) else {},
            }

        def _unavailable(reason: str, explanation: str, unified_surface) -> dict:
            return {
                "audit_available": False,
                "audit_mode": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK",
                "lock_state": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_UNAVAILABLE",
                "reason": reason,
                "supporting_surfaces": {
                    "unified_system_consumer_posture_summary": unified_surface,
                },
                "checks_run": 0,
                "checks_passed": 0,
                "checks_failed": 0,
                "check_results": [],
                "contract_surface": {
                    "required_surfaces": {
                        "unified_system_consumer_posture_api_present": callable(getattr(self, _UNIFIED_API, None)),
                    },
                    "preserved_posture_states": sorted(_CANONICAL_STATES),
                    "no_new_predicates_above_unified_surface": True,
                },
                "warnings": [],
                "explanation_lines": [explanation],
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        if not callable(getattr(self, _UNIFIED_API, None)):
            return _unavailable(
                "REQUIRED_SURFACE_MISSING",
                "Required unified posture surface missing: get_unified_system_consumer_posture_summary.",
                None,
            )

        try:
            unified = self.get_unified_system_consumer_posture_summary()
        except Exception as exc:
            return _unavailable(
                "REQUIRED_SURFACE_UNUSABLE",
                f"get_unified_system_consumer_posture_summary() raised {type(exc).__name__}.",
                None,
            )

        if not isinstance(unified, dict):
            return _unavailable(
                "REQUIRED_SURFACE_SHAPE_INVALID",
                "Unified posture surface returned non-dict output.",
                unified,
            )

        checks: list[dict] = []

        mode_ok = unified.get("summary_mode") == "UNIFIED_SYSTEM_CONSUMER_POSTURE"
        checks.append(
            _check(
                "UNIFIED_SUMMARY_MODE_PRESENT",
                mode_ok,
                "MODE_OK" if mode_ok else "MODE_MISMATCH",
                {"summary_mode": unified.get("summary_mode")},
            )
        )

        state = str(unified.get("summary_state", "SYSTEM_CONSUMER_UNAVAILABLE"))
        state_ok = state in _CANONICAL_STATES
        checks.append(
            _check(
                "UNIFIED_SUMMARY_STATE_CANONICAL",
                state_ok,
                "STATE_CANONICAL" if state_ok else "STATE_NON_CANONICAL",
                {"summary_state": state},
            )
        )

        available = bool(unified.get("summary_available", False))
        unavailable_shape_ok = True
        if not available:
            unavailable_shape_ok = state == "SYSTEM_CONSUMER_UNAVAILABLE"
        checks.append(
            _check(
                "UNAVAILABLE_FAIL_CLOSED_SHAPE",
                unavailable_shape_ok,
                "UNAVAILABLE_SHAPE_OK" if unavailable_shape_ok else "UNAVAILABLE_SHAPE_MISMATCH",
                {"summary_available": available, "summary_state": state},
            )
        )

        guard_violations = [k for k in _GUARDRAILS if unified.get(k) is not False]
        checks.append(
            _check(
                "READ_ONLY_GUARDRAILS_FALSE",
                len(guard_violations) == 0,
                "ALL_GUARDRAILS_FALSE" if len(guard_violations) == 0 else "GUARDRAIL_FLAG_VIOLATION",
                {"violations": guard_violations},
            )
        )

        checks_run = len(checks)
        checks_passed = sum(1 for c in checks if c["passed"])
        checks_failed = checks_run - checks_passed

        warnings = list(unified.get("warnings", [])) if isinstance(unified.get("warnings"), list) else []
        if guard_violations:
            warnings.append("GUARDRAIL_FLAG_VIOLATION")

        if checks_failed == 0:
            lock_state = "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCKED"
            reason = "ALL_CONSISTENCY_CHECKS_PASSED"
            explanation_lines = [
                "Unified consumer posture stage-lock checks passed."
            ]
        else:
            lock_state = "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_INCONSISTENT"
            reason = "CONSISTENCY_CHECK_FAILED"
            failed_names = [c["check_name"] for c in checks if not c["passed"]]
            explanation_lines = [
                "Unified consumer posture stage-lock inconsistency detected.",
                "Failed checks: " + ", ".join(failed_names),
            ]

        return {
            "audit_available": True,
            "audit_mode": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK",
            "lock_state": lock_state,
            "reason": reason,
            "supporting_surfaces": {
                "unified_system_consumer_posture_summary": unified,
            },
            "checks_run": checks_run,
            "checks_passed": checks_passed,
            "checks_failed": checks_failed,
            "check_results": checks,
            "contract_surface": {
                "required_surfaces": {
                    "unified_system_consumer_posture_api_present": True,
                },
                "preserved_posture_states": sorted(_CANONICAL_STATES),
                "no_new_predicates_above_unified_surface": True,
            },
            "warnings": sorted(set(warnings)),
            "explanation_lines": explanation_lines,
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_unified_system_consumer_summary(self) -> dict:
        """
        Unified System Consumer Summary / Delivery v1.2.
        Pure read-only packaging layer over unified posture summary and its stage-lock audit.
        """
        _POSTURE_API = "get_unified_system_consumer_posture_summary"
        _STAGE_LOCK_API = "get_unified_system_consumer_posture_stage_lock_audit"

        def _unavailable(
            *,
            summary_reason: str,
            explanation: str,
            posture_surface,
            stage_lock_surface,
            warnings: list[str],
        ) -> dict:
            return {
                "summary_available": False,
                "summary_mode": "UNIFIED_SYSTEM_CONSUMER_SUMMARY",
                "summary_state": "SYSTEM_CONSUMER_UNAVAILABLE",
                "summary_reason": summary_reason,
                "packaged_consumer_posture": {
                    "unified_posture_state": "SYSTEM_CONSUMER_UNAVAILABLE",
                    "unified_posture_reason": "UNIFIED_POSTURE_UNAVAILABLE",
                    "unified_stage_lock_state": "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_UNAVAILABLE",
                    "unified_stage_lock_reason": "UNIFIED_STAGE_LOCK_UNAVAILABLE",
                },
                "supporting_surfaces": {
                    "unified_system_consumer_posture_summary": posture_surface,
                    "unified_system_consumer_posture_stage_lock_audit": stage_lock_surface,
                },
                "explanation_lines": [explanation],
                "warnings": sorted(set(warnings)),
                "lineage_mutation_performed": False,
                "event_creation_performed": False,
                "history_rewrite_performed": False,
            }

        required_missing = []
        if not callable(getattr(self, _POSTURE_API, None)):
            required_missing.append(_POSTURE_API)
        if not callable(getattr(self, _STAGE_LOCK_API, None)):
            required_missing.append(_STAGE_LOCK_API)
        if required_missing:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_MISSING",
                explanation=(
                    "Required unified consumer summary surface missing: "
                    + ", ".join(required_missing)
                    + "."
                ),
                posture_surface=None,
                stage_lock_surface=None,
                warnings=["REQUIRED_SURFACE_MISSING"],
            )

        posture_surface = None
        stage_lock_surface = None
        try:
            posture_surface = self.get_unified_system_consumer_posture_summary()
        except Exception as exc:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_unified_system_consumer_posture_summary() raised {type(exc).__name__}.",
                posture_surface=None,
                stage_lock_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "UNIFIED_POSTURE_CALL_FAILED"],
            )
        try:
            stage_lock_surface = self.get_unified_system_consumer_posture_stage_lock_audit()
        except Exception as exc:
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_UNUSABLE",
                explanation=f"get_unified_system_consumer_posture_stage_lock_audit() raised {type(exc).__name__}.",
                posture_surface=posture_surface,
                stage_lock_surface=None,
                warnings=["REQUIRED_SURFACE_UNUSABLE", "UNIFIED_STAGE_LOCK_CALL_FAILED"],
            )

        posture_shape_ok = (
            isinstance(posture_surface, dict)
            and isinstance(posture_surface.get("summary_state"), str)
            and isinstance(posture_surface.get("summary_reason"), str)
        )
        stage_lock_shape_ok = (
            isinstance(stage_lock_surface, dict)
            and isinstance(stage_lock_surface.get("lock_state"), str)
            and isinstance(stage_lock_surface.get("reason"), str)
        )
        if not posture_shape_ok or not stage_lock_shape_ok:
            bad = []
            if not posture_shape_ok:
                bad.append("UNIFIED_POSTURE_SURFACE_SHAPE_INVALID")
            if not stage_lock_shape_ok:
                bad.append("UNIFIED_STAGE_LOCK_SURFACE_SHAPE_INVALID")
            return _unavailable(
                summary_reason="REQUIRED_SURFACE_SHAPE_INVALID",
                explanation="Required unified consumer summary surface shape invalid: " + ", ".join(bad) + ".",
                posture_surface=posture_surface,
                stage_lock_surface=stage_lock_surface,
                warnings=bad,
            )

        posture_state = str(posture_surface.get("summary_state", "SYSTEM_CONSUMER_UNAVAILABLE"))
        posture_reason = str(posture_surface.get("summary_reason", "UNIFIED_POSTURE_REASON_MISSING"))
        stage_lock_state = str(
            stage_lock_surface.get("lock_state", "UNIFIED_SYSTEM_CONSUMER_STAGE_LOCK_UNAVAILABLE")
        )
        stage_lock_reason = str(stage_lock_surface.get("reason", "UNIFIED_STAGE_LOCK_REASON_MISSING"))

        warnings = []
        if isinstance(posture_surface.get("warnings"), list):
            warnings.extend(posture_surface.get("warnings", []))
        if isinstance(stage_lock_surface.get("warnings"), list):
            warnings.extend(stage_lock_surface.get("warnings", []))

        explanation_lines = [
            f"Unified summary state: {posture_state}",
            f"Unified summary reason: {posture_reason}",
            f"Unified stage lock state: {stage_lock_state}",
            f"Unified stage lock reason: {stage_lock_reason}",
        ]

        return {
            "summary_available": True,
            "summary_mode": "UNIFIED_SYSTEM_CONSUMER_SUMMARY",
            "summary_state": posture_state,
            "summary_reason": posture_reason,
            "packaged_consumer_posture": {
                "unified_posture_state": posture_state,
                "unified_posture_reason": posture_reason,
                "unified_stage_lock_state": stage_lock_state,
                "unified_stage_lock_reason": stage_lock_reason,
            },
            "supporting_surfaces": {
                "unified_system_consumer_posture_summary": posture_surface,
                "unified_system_consumer_posture_stage_lock_audit": stage_lock_surface,
            },
            "explanation_lines": explanation_lines,
            "warnings": sorted(set(warnings)),
            "lineage_mutation_performed": False,
            "event_creation_performed": False,
            "history_rewrite_performed": False,
        }

    def get_transition_report(self, event_id: str, max_depth: int = 8) -> dict:
        """
        Returns a compact, structured transition report for one ledger event.

        Data sources:
        - durable event ledger
        - current family records
        - existing ancestry query APIs
        - existing lineage integrity audit API (event-scoped filter)
        """
        if max_depth < 0:
            max_depth = 0

        evt, duplicate_count = self._get_ledger_event_by_id(event_id)
        if evt is None:
            return {
                "event_id": event_id,
                "found": False,
                "max_depth": max_depth,
                "reason": "EVENT_NOT_FOUND",
                "event_identity": None,
                "structural_gate_rationale": None,
                "participants": None,
                "before_after_family_state": None,
                "lineage_links": None,
                "integrity_summary": None,
                "geometry_fit_summary": None,
                "topology_summary": None,
            }

        source_ids = [x for x in evt.get("source_family_ids", []) if isinstance(x, str) and x]
        successor_ids = [x for x in evt.get("successor_family_ids", []) if isinstance(x, str) and x]
        involved_family_ids = sorted(set(source_ids + successor_ids))

        event_identity = {
            "event_id": str(evt.get("event_id", "")),
            "event_type": evt.get("event_type"),
            "event_order": evt.get("event_order"),
            "ledger_write_order": evt.get("ledger_write_order"),
            "ledger_timestamp_utc": evt.get("ledger_timestamp_utc"),
            "duplicate_event_id_count_in_ledger": int(duplicate_count),
        }

        structural_gate_rationale = {
            "gate_summary": dict(evt.get("gate_summary", {})) if isinstance(evt.get("gate_summary"), dict) else {},
            "rationale": evt.get("rationale"),
        }

        member_summary = self._build_event_member_summary(evt)
        participants = {
            "source_family_ids": list(source_ids),
            "successor_family_ids": list(successor_ids),
            "parent_family_id": evt.get("parent_family_id"),
            "successor_family_id": evt.get("successor_family_id"),
            "member_summary": member_summary,
        }

        before_after_family_state = {
            "current_state_snapshot_only": True,
            "source_family_states": [self._build_family_state_snapshot(fam_id) for fam_id in source_ids],
            "successor_family_states": [self._build_family_state_snapshot(fam_id) for fam_id in successor_ids],
        }

        lineage_links = {
            "parent_source_family_ids": list(source_ids),
            "successor_family_ids": list(successor_ids),
            "source_to_successor_edges": [
                {
                    "source_family_id": src,
                    "successor_family_id": succ,
                    "event_id": evt.get("event_id"),
                    "event_type": evt.get("event_type"),
                }
                for src in source_ids
                for succ in successor_ids
            ],
            "successor_origins": [self.get_family_origin(fam_id) for fam_id in successor_ids],
            "source_successors": [
                self.get_family_successors(fam_id, recursive=False, max_depth=max_depth)
                for fam_id in source_ids
            ],
        }

        integrity_summary = self._build_event_scoped_integrity_summary(
            event_id=event_id,
            involved_family_ids=involved_family_ids,
            max_depth=max_depth,
        )

        return {
            "event_id": event_id,
            "found": True,
            "max_depth": max_depth,
            "event_identity": event_identity,
            "structural_gate_rationale": structural_gate_rationale,
            "participants": participants,
            "before_after_family_state": before_after_family_state,
            "lineage_links": lineage_links,
            "integrity_summary": integrity_summary,
            "geometry_fit_summary": self.get_transition_geometry_fit(event_id),
            "topology_summary": self.get_transition_topology_audit(event_id),
        }

    def get_event_dossier(self, event_id: str, max_depth: int = 8) -> dict:
        """Alias for get_transition_report for report-style usage."""
        return self.get_transition_report(event_id=event_id, max_depth=max_depth)

    def get_boundary_status(self, symbol_id: str) -> Optional[str]:
        """Returns the earned persistent boundary status for a symbol, if any."""
        return self._earned_boundary_statuses.get(symbol_id)

    def _check_for_fracture(self, family_id: str) -> None:
        """
        Analyzes a family for internal structural separation or over-breadth.
        Updates fracture_counter and fracture_status if thresholds are exceeded.
        """
        record = self._families.get(family_id)
        if not record or len(record.member_symbol_ids) < 2:
            return

        # 1. Check for over-breadth (average spread)
        avg_spread = sum(record.current_spread.values()) / len(record.current_spread)
        over_broad = avg_spread > self.MAX_COHERENCE_SPREAD

        # 2. Check for internal distance (separation between members)
        # Identify if any members cluster around different internal centers
        subgroup_detected = False
        if len(record.member_symbol_ids) >= 2:
            subgroup_detected = self._detect_subgroups(family_id)
        
        if subgroup_detected:
            record.subgroup_evidence_counter += 1
            if record.subgroup_evidence_counter >= self.SUBGROUP_PERSISTENCE_THRESHOLD:
                record.subgroup_count = 2
            else:
                record.subgroup_count = 1
        else:
            if record.subgroup_evidence_counter > 0:
                record.subgroup_evidence_counter -= 1
            if record.subgroup_evidence_counter == 0:
                record.subgroup_count = 1

        if over_broad or record.subgroup_count > 1:
            record.fracture_counter += 1
            if record.fracture_counter >= self.FRACTURE_PERSISTENCE_THRESHOLD:
                record.fracture_status = "FAMILY_SPLIT_READY"
            else:
                record.fracture_status = "FAMILY_FRACTURE_HOLD"
        else:
            # Coherent enough for now
            if record.fracture_counter > 0:
                record.fracture_counter -= 1
            if record.fracture_counter == 0:
                record.fracture_status = None

        # Actual family fission requires BOTH persistent SPLIT_READY AND persistent dual-center evidence,
        # plus an additional stable-partition persistence counter. This is intentionally conservative.
        self._check_for_fission(family_id)

    def _detect_subgroups(self, family_id: str) -> bool:
        """
        Determines if a family's members appear to be organized around 
        two internal centers rather than one broad cloud.
        
        Uses a deterministic pairwise distance heuristic to detect bifurcation.
        """
        return self._compute_subgroup_partition(family_id) is not None

    def _canonicalize_partition(self, group_a: List[str], group_b: List[str]) -> Tuple[List[str], List[str], str]:
        """
        Returns (canon_group_1, canon_group_2, partition_key) where the ordering is stable
        regardless of which center was picked first.
        """
        a_sorted = sorted(group_a)
        b_sorted = sorted(group_b)
        k1 = "|".join(a_sorted)
        k2 = "|".join(b_sorted)
        if k1 <= k2:
            return a_sorted, b_sorted, f"{k1}||{k2}"
        return b_sorted, a_sorted, f"{k2}||{k1}"

    def _compute_subgroup_partition_from_member_ids(self, member_ids: List[str]) -> Optional[Tuple[List[str], List[str]]]:
        """
        First-pass deterministic dual-center partition for an arbitrary member-id set.
        Returns None when evidence is insufficient or partition is degenerate.
        """
        if len(member_ids) < 2:
            return None
        try:
            member_sigs = [self._symbol_signatures[m_id] for m_id in member_ids]
        except KeyError:
            # Incomplete symbol geometry cache: fail closed.
            return None

        # 1. Calculate all pairwise distances between members.
        max_dist = 0.0
        p1_idx = 0
        p2_idx = 0
        for i in range(len(member_sigs)):
            for j in range(i + 1, len(member_sigs)):
                d = self._calculate_distance(member_sigs[i], member_sigs[j])
                if d > max_dist:
                    max_dist = d
                    p1_idx = i
                    p2_idx = j

        # 2. If max member distance is not large enough, fail closed.
        if max_dist < self.SUBGROUP_SEPARATION_THRESHOLD:
            return None

        # 3. Use the two most-distant members as candidate internal centers.
        center1 = member_sigs[p1_idx]
        center2 = member_sigs[p2_idx]
        total_dist_to_nearest = 0.0
        for sig in member_sigs:
            d1 = self._calculate_distance(sig, center1)
            d2 = self._calculate_distance(sig, center2)
            total_dist_to_nearest += min(d1, d2)
        avg_internal_dist = total_dist_to_nearest / len(member_sigs)

        if not (max_dist > (avg_internal_dist * self.SUBGROUP_TIGHTNESS_RATIO) and max_dist > 0.1):
            return None

        # 4. Deterministic nearest-center partition.
        group_1: list[str] = []
        group_2: list[str] = []
        for m_id, sig in zip(member_ids, member_sigs):
            d1 = self._calculate_distance(sig, center1)
            d2 = self._calculate_distance(sig, center2)
            if d1 <= d2:
                group_1.append(m_id)
            else:
                group_2.append(m_id)

        if not group_1 or not group_2:
            return None
        if min(len(group_1), len(group_2)) < self.MIN_SUBGROUP_MEMBERS_FOR_DETECTION:
            return None
        return group_1, group_2

    def _compute_subgroup_partition(self, family_id: str) -> Optional[Tuple[List[str], List[str]]]:
        """
        If a stable dual-center structure is present, returns a deterministic partition
        of member_symbol_ids into two non-empty groups (by nearest-center assignment).

        Returns None if evidence is insufficient or a non-degenerate partition cannot be made.
        """
        record = self._families.get(family_id)
        if not record or len(record.member_symbol_ids) < 2:
            return None
        return self._compute_subgroup_partition_from_member_ids(record.member_symbol_ids)

    def _compute_group_centroid(self, member_ids: List[str]) -> dict[str, float]:
        axes = ["axis_a", "axis_b", "axis_c", "axis_d"]
        if not member_ids:
            return {a: 0.0 for a in axes}
        out = {a: 0.0 for a in axes}
        for m_id in member_ids:
            sig = self._symbol_signatures[m_id]
            for a in axes:
                out[a] += float(sig.get(a, 0.0))
        for a in axes:
            out[a] /= float(len(member_ids))
        return out

    def _compute_group_spread_avg(self, member_ids: List[str]) -> dict[str, float]:
        axes = ["axis_a", "axis_b", "axis_c", "axis_d"]
        if not member_ids:
            return {a: 0.0 for a in axes}
        out = {a: 0.0 for a in axes}
        for m_id in member_ids:
            spr = self._symbol_spreads.get(m_id, {})
            for a in axes:
                out[a] += float(spr.get(a, 0.0))
        for a in axes:
            out[a] /= float(len(member_ids))
        return out

    def _compute_avg_spread_for_family(self, family_id: str) -> float:
        record = self._families.get(family_id)
        if not record or not record.current_spread:
            return 0.0
        return sum(record.current_spread.values()) / len(record.current_spread)

    def _compute_max_pairwise_distance(self, member_ids: List[str]) -> float:
        if len(member_ids) < 2:
            return 0.0
        max_dist = 0.0
        for i in range(len(member_ids)):
            sig_i = self._symbol_signatures.get(member_ids[i])
            if sig_i is None:
                return 999.0
            for j in range(i + 1, len(member_ids)):
                sig_j = self._symbol_signatures.get(member_ids[j])
                if sig_j is None:
                    return 999.0
                d = self._calculate_distance(sig_i, sig_j)
                if d > max_dist:
                    max_dist = d
        return max_dist

    def _pair_key(self, fam_a: str, fam_b: str) -> str:
        return f"{fam_a}||{fam_b}" if fam_a <= fam_b else f"{fam_b}||{fam_a}"

    def _append_durable_event(self, event_record: dict) -> None:
        """
        Appends a single event record to the durable JSONL ledger.

        Fail-closed behavior: raises RuntimeError on write failure so caller can
        avoid applying topology transitions without durable audit.
        """
        event_id = str(event_record.get("event_id", ""))
        if not event_id:
            raise RuntimeError("Durable ledger write refused: missing event_id.")

        # Prevent duplicate write attempts for the same in-memory event.
        if event_id in self._durable_written_event_ids:
            return

        self._durable_write_counter += 1
        durable_record = dict(event_record)
        durable_record["ledger_write_order"] = self._durable_write_counter
        durable_record["ledger_timestamp_utc"] = datetime.now(timezone.utc).isoformat()

        path = self._durable_ledger_path
        directory = os.path.dirname(path)
        try:
            if directory:
                os.makedirs(directory, exist_ok=True)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(durable_record, sort_keys=True, separators=(",", ":")) + "\n")
        except OSError as exc:
            raise RuntimeError(f"Durable ledger write failed for event {event_id}: {exc}") from exc

        self._durable_written_event_ids.add(event_id)

    def _check_for_reunion_candidates(self) -> None:
        """
        Evaluates active family pairs for conservative structural reunion.
        Reunion is intentionally stricter than one favorable closeness observation.
        """
        active_ids = sorted(
            [fam_id for fam_id, rec in self._families.items() if rec.lifecycle_status == "FAMILY_ACTIVE"]
        )
        active_set = set(active_ids)

        # Clean up stale pending pair entries where one side is no longer active.
        stale_keys: list[str] = []
        for key in self._pending_reunion:
            parts = key.split("||")
            if len(parts) != 2 or parts[0] not in active_set or parts[1] not in active_set:
                stale_keys.append(key)
        for key in stale_keys:
            del self._pending_reunion[key]

        for i in range(len(active_ids)):
            for j in range(i + 1, len(active_ids)):
                fam_a = active_ids[i]
                fam_b = active_ids[j]
                key = self._pair_key(fam_a, fam_b)

                rec_a = self._families[fam_a]
                rec_b = self._families[fam_b]

                # Source family minimum size gate.
                if len(rec_a.member_symbol_ids) < self.MIN_MEMBERS_PER_SOURCE_FOR_REUNION:
                    self._pending_reunion.pop(key, None)
                    continue
                if len(rec_b.member_symbol_ids) < self.MIN_MEMBERS_PER_SOURCE_FOR_REUNION:
                    self._pending_reunion.pop(key, None)
                    continue

                center_dist = self._calculate_distance(rec_a.current_signature, rec_b.current_signature)
                avg_spread_a = self._compute_avg_spread_for_family(fam_a)
                avg_spread_b = self._compute_avg_spread_for_family(fam_b)
                spread_delta = abs(avg_spread_a - avg_spread_b)
                envelope_overlap = center_dist <= (avg_spread_a + avg_spread_b)
                center_close = center_dist <= self.REUNION_CENTER_DISTANCE_THRESHOLD
                spread_compatible = spread_delta <= self.REUNION_SPREAD_DELTA_THRESHOLD

                combined_members = list(rec_a.member_symbol_ids) + list(rec_b.member_symbol_ids)
                if len(set(combined_members)) != len(combined_members):
                    # Fail closed if one-family-only integrity is already violated.
                    self._pending_reunion.pop(key, None)
                    continue

                combined_spread = self._compute_group_spread_avg(combined_members)
                combined_avg_spread = sum(combined_spread.values()) / len(combined_spread)
                combined_max_internal = self._compute_max_pairwise_distance(combined_members)
                combined_coherent = (
                    combined_avg_spread <= self.REUNION_COMBINED_MAX_SPREAD
                    and combined_max_internal <= self.REUNION_COMBINED_MAX_INTERNAL_DISTANCE
                )

                if center_close and spread_compatible and envelope_overlap and combined_coherent:
                    self._pending_reunion[key] = self._pending_reunion.get(key, 0) + 1
                else:
                    self._pending_reunion.pop(key, None)
                    continue

                if self._pending_reunion[key] < self.REUNION_PERSISTENCE_THRESHOLD:
                    continue

                self._execute_family_reunion(
                    source_family_a=fam_a,
                    source_family_b=fam_b,
                    rationale=(
                        "Actual family reunion executed after persistent center proximity, "
                        "spread compatibility, envelope overlap, and combined coherence."
                    ),
                )
                # Topology changed. Stop and reevaluate on next observation.
                return

    def _check_for_fission(self, family_id: str) -> None:
        record = self._families.get(family_id)
        if not record:
            return
        if record.lifecycle_status != "FAMILY_ACTIVE":
            return

        # Must be in persistent SPLIT_READY lane AND have persistent dual-center evidence.
        if record.fracture_status != "FAMILY_SPLIT_READY":
            record.fission_candidate_counter = 0
            record.fission_partition_key = None
            return
        if record.subgroup_count != 2:
            record.fission_candidate_counter = 0
            record.fission_partition_key = None
            return
        if len(record.member_symbol_ids) < self.MIN_MEMBERS_FOR_FISSION:
            # Under-splitting bias: refuse fission on tiny families.
            record.fission_candidate_counter = 0
            record.fission_partition_key = None
            return

        partition = self._compute_subgroup_partition(family_id)
        if partition is None:
            if record.fission_candidate_counter > 0:
                record.fission_candidate_counter -= 1
            if record.fission_candidate_counter == 0:
                record.fission_partition_key = None
            return

        g1, g2 = partition
        g1c, g2c, key = self._canonicalize_partition(g1, g2)
        if min(len(g1c), len(g2c)) < self.MIN_SUBGROUP_MEMBERS_FOR_FISSION:
            record.fission_candidate_counter = 0
            record.fission_partition_key = None
            return
        if record.fission_partition_key == key:
            record.fission_candidate_counter += 1
        else:
            record.fission_partition_key = key
            record.fission_candidate_counter = 1

        if record.fission_candidate_counter < self.FISSION_PERSISTENCE_THRESHOLD:
            return

        self._execute_family_fission(
            parent_family_id=family_id,
            group_1_member_ids=g1c,
            group_2_member_ids=g2c,
            rationale=(
                "Actual family fission executed after persistent SPLIT_READY posture, "
                "persistent dual-center evidence, and stable subgroup partition persistence."
            ),
        )

    def _capture_family_pressure_if_available(self, family_id: str) -> tuple[Optional[dict], str]:
        """
        Best-effort event-write-time pressure capture for one family.
        Returns (captured_pressure_or_none, capture_status).
        """
        try:
            forecast = self.get_family_pressure_forecast(family_id)
        except Exception as exc:
            return None, f"PRESSURE_CAPTURE_EXCEPTION:{type(exc).__name__}"

        if not isinstance(forecast, dict):
            return None, "PRESSURE_CAPTURE_OUTPUT_INVALID"
        if bool(forecast.get("forecast_available", False)):
            return forecast, "PRESSURE_CAPTURED"
        return None, "PRESSURE_UNAVAILABLE"

    def _build_event_write_time_pressure_snapshot(
        self,
        *,
        source_family_ids: list[str],
        successor_records: list[NeutralFamilyRecordV1],
    ) -> dict:
        """
        Captures event-local pressure posture at write time from recoverable current evidence.
        Best-effort and fail-closed: never raises; may return partial or failed capture.
        """
        pre_map: dict[str, dict] = {}
        post_map: dict[str, dict] = {}
        pre_status_by_family: dict[str, str] = {}
        post_status_by_family: dict[str, str] = {}

        # Pre-event capture from currently active source families.
        for fam_id in source_family_ids:
            captured, status = self._capture_family_pressure_if_available(fam_id)
            pre_status_by_family[fam_id] = status
            if captured is not None:
                pre_map[fam_id] = captured

        # Post-event capture from successor records by temporary in-memory staging only.
        staged_ids: list[str] = []
        for rec in successor_records:
            fam_id = rec.family_id
            if fam_id in self._families:
                post_status_by_family[fam_id] = "PRESSURE_STAGE_COLLISION"
                continue
            self._families[fam_id] = rec
            staged_ids.append(fam_id)

        try:
            for rec in successor_records:
                fam_id = rec.family_id
                if post_status_by_family.get(fam_id) == "PRESSURE_STAGE_COLLISION":
                    continue
                captured, status = self._capture_family_pressure_if_available(fam_id)
                post_status_by_family[fam_id] = status
                if captured is not None:
                    post_map[fam_id] = captured
        finally:
            for fam_id in staged_ids:
                self._families.pop(fam_id, None)

        pre_payload = None
        if pre_map:
            pre_payload = {
                "family_ids": sorted(pre_map.keys()),
                "family_pressure_by_id": pre_map,
            }
        post_payload = None
        if post_map:
            post_payload = {
                "family_ids": sorted(post_map.keys()),
                "family_pressure_by_id": post_map,
            }

        capture_succeeded = bool(pre_payload is not None or post_payload is not None)
        if pre_payload is not None and post_payload is not None:
            capture_reason = "PRESSURE_CAPTURE_FULL"
        elif capture_succeeded:
            capture_reason = "PRESSURE_CAPTURE_PARTIAL"
        else:
            capture_reason = "PRESSURE_CAPTURE_FAILED"

        return {
            "pre_event_pressure": pre_payload,
            "post_event_pressure": post_payload,
            "capture_attempted": True,
            "capture_succeeded": capture_succeeded,
            "capture_mode": "EVENT_WRITE_TIME",
            "capture_reason": capture_reason,
            "pre_capture_status_by_family": pre_status_by_family,
            "post_capture_status_by_family": post_status_by_family,
        }

    def _execute_family_fission(self, parent_family_id: str, group_1_member_ids: List[str], group_2_member_ids: List[str], rationale: str) -> None:
        parent = self._families.get(parent_family_id)
        if not parent:
            return
        if parent.lifecycle_status != "FAMILY_ACTIVE":
            return
        if not group_1_member_ids or not group_2_member_ids:
            return

        # Allocate observation_count proportionally (heuristic). This is intentionally approximate.
        total_members = max(1, len(group_1_member_ids) + len(group_2_member_ids))
        p_obs = max(0, int(parent.observation_count))
        if p_obs > 0:
            g1_obs = max(1, int(round(p_obs * (len(group_1_member_ids) / total_members))))
            g2_obs = max(1, int(round(p_obs * (len(group_2_member_ids) / total_members))))
        else:
            g1_obs = max(1, len(group_1_member_ids))
            g2_obs = max(1, len(group_2_member_ids))

        self._fission_event_counter += 1
        evt_id = f"fission_evt_{self._fission_event_counter:04d}"

        # Mint successor family IDs
        self._family_counter += 1
        fam_1 = f"fam_{self._family_counter:02d}"
        self._family_counter += 1
        fam_2 = f"fam_{self._family_counter:02d}"

        fam_1_sig = self._compute_group_centroid(group_1_member_ids)
        fam_2_sig = self._compute_group_centroid(group_2_member_ids)
        fam_1_spr = self._compute_group_spread_avg(group_1_member_ids)
        fam_2_spr = self._compute_group_spread_avg(group_2_member_ids)

        rec_1 = NeutralFamilyRecordV1(
            family_id=fam_1,
            member_symbol_ids=list(group_1_member_ids),
            mint_signature=fam_1_sig.copy(),
            current_signature=fam_1_sig.copy(),
            mint_spread=fam_1_spr.copy(),
            current_spread=fam_1_spr.copy(),
            observation_count=g1_obs,
            lineage_parent_family_id=parent_family_id,
            lineage_fission_event_id=evt_id,
            fission_event_ids=[evt_id],
        )
        rec_2 = NeutralFamilyRecordV1(
            family_id=fam_2,
            member_symbol_ids=list(group_2_member_ids),
            mint_signature=fam_2_sig.copy(),
            current_signature=fam_2_sig.copy(),
            mint_spread=fam_2_spr.copy(),
            current_spread=fam_2_spr.copy(),
            observation_count=g2_obs,
            lineage_parent_family_id=parent_family_id,
            lineage_fission_event_id=evt_id,
            fission_event_ids=[evt_id],
        )

        evt = {
            "event_id": evt_id,
            "event_type": "FAMILY_FISSION_V1",
            "event_order": self._fission_event_counter,
            "source_family_ids": [parent_family_id],
            "successor_family_ids": [fam_1, fam_2],
            "parent_family_id": parent_family_id,
            "parent_lifecycle_post": "FAMILY_INACTIVE_SUCCESSOR_SPLIT",
            "gate_summary": {
                "requires_fracture_status": "FAMILY_SPLIT_READY",
                "requires_subgroup_count": 2,
                "min_members_for_fission": int(self.MIN_MEMBERS_FOR_FISSION),
                "min_subgroup_members_for_detection": int(self.MIN_SUBGROUP_MEMBERS_FOR_DETECTION),
                "min_subgroup_members_for_fission": int(self.MIN_SUBGROUP_MEMBERS_FOR_FISSION),
                "subgroup_persistence_threshold": int(self.SUBGROUP_PERSISTENCE_THRESHOLD),
                "fracture_persistence_threshold": int(self.FRACTURE_PERSISTENCE_THRESHOLD),
                "fission_persistence_threshold": int(self.FISSION_PERSISTENCE_THRESHOLD),
            },
            "partition": {
                "group_1_member_ids": list(rec_1.member_symbol_ids),
                "group_2_member_ids": list(rec_2.member_symbol_ids),
            },
            "pressure_snapshot": self._build_event_write_time_pressure_snapshot(
                source_family_ids=[parent_family_id],
                successor_records=[rec_1, rec_2],
            ),
            "rationale": rationale,
        }

        # Fail closed: do not apply topology mutation if durable ledger write fails.
        self._append_durable_event(evt)

        # Update one-family-only membership map
        for m_id in rec_1.member_symbol_ids:
            self._symbol_to_family[m_id] = fam_1
        for m_id in rec_2.member_symbol_ids:
            self._symbol_to_family[m_id] = fam_2

        # Parent becomes inactive/historical-only, preserving explicit lineage and membership snapshot.
        parent.historical_member_symbol_ids = list(parent.member_symbol_ids)
        parent.member_symbol_ids = []
        parent.lifecycle_status = "FAMILY_INACTIVE_SUCCESSOR_SPLIT"
        parent.inactive_reason = f"Fissioned into successors {fam_1} and {fam_2} under conservative structural gating."
        parent.lineage_successor_family_ids = [fam_1, fam_2]
        parent.fission_event_ids.append(evt_id)
        parent.fission_candidate_counter = 0
        parent.fission_partition_key = None

        self._families[fam_1] = rec_1
        self._families[fam_2] = rec_2

        self._fission_events.append(evt)

    def _execute_family_reunion(self, source_family_a: str, source_family_b: str, rationale: str) -> None:
        rec_a = self._families.get(source_family_a)
        rec_b = self._families.get(source_family_b)
        if not rec_a or not rec_b:
            return
        if rec_a.lifecycle_status != "FAMILY_ACTIVE" or rec_b.lifecycle_status != "FAMILY_ACTIVE":
            return

        combined_members = sorted(list(rec_a.member_symbol_ids) + list(rec_b.member_symbol_ids))
        if not combined_members:
            return
        if len(set(combined_members)) != len(combined_members):
            return

        combined_sig = self._compute_group_centroid(combined_members)
        combined_spr = self._compute_group_spread_avg(combined_members)
        combined_avg_spread = sum(combined_spr.values()) / len(combined_spr)
        combined_max_internal = self._compute_max_pairwise_distance(combined_members)
        if combined_avg_spread > self.REUNION_COMBINED_MAX_SPREAD:
            return
        if combined_max_internal > self.REUNION_COMBINED_MAX_INTERNAL_DISTANCE:
            return

        self._reunion_event_counter += 1
        evt_id = f"reunion_evt_{self._reunion_event_counter:04d}"

        self._family_counter += 1
        reunited_id = f"fam_{self._family_counter:02d}"
        reunited_obs = max(1, int(rec_a.observation_count) + int(rec_b.observation_count))

        reunited = NeutralFamilyRecordV1(
            family_id=reunited_id,
            member_symbol_ids=list(combined_members),
            mint_signature=combined_sig.copy(),
            current_signature=combined_sig.copy(),
            mint_spread=combined_spr.copy(),
            current_spread=combined_spr.copy(),
            observation_count=reunited_obs,
            lineage_parent_family_ids=[source_family_a, source_family_b],
            lineage_reunion_event_id=evt_id,
            reunion_event_ids=[evt_id],
        )

        evt = {
            "event_id": evt_id,
            "event_type": "FAMILY_REUNION_V1",
            "event_order": self._reunion_event_counter,
            "source_family_ids": [source_family_a, source_family_b],
            "successor_family_ids": [reunited_id],
            "successor_family_id": reunited_id,
            "source_lifecycle_post": "FAMILY_INACTIVE_SUCCESSOR_REUNION",
            "gate_summary": {
                "reunion_center_distance_threshold": float(self.REUNION_CENTER_DISTANCE_THRESHOLD),
                "reunion_spread_delta_threshold": float(self.REUNION_SPREAD_DELTA_THRESHOLD),
                "reunion_persistence_threshold": int(self.REUNION_PERSISTENCE_THRESHOLD),
                "reunion_combined_max_spread": float(self.REUNION_COMBINED_MAX_SPREAD),
                "reunion_combined_max_internal_distance": float(self.REUNION_COMBINED_MAX_INTERNAL_DISTANCE),
                "min_members_per_source_for_reunion": int(self.MIN_MEMBERS_PER_SOURCE_FOR_REUNION),
            },
            "members": {
                "source_a_member_ids": list(rec_a.member_symbol_ids),
                "source_b_member_ids": list(rec_b.member_symbol_ids),
                "reunited_member_ids": list(reunited.member_symbol_ids),
            },
            "pressure_snapshot": self._build_event_write_time_pressure_snapshot(
                source_family_ids=[source_family_a, source_family_b],
                successor_records=[reunited],
            ),
            "rationale": rationale,
        }

        # Fail closed: do not apply topology mutation if durable ledger write fails.
        self._append_durable_event(evt)

        for m_id in reunited.member_symbol_ids:
            self._symbol_to_family[m_id] = reunited_id

        # Source families become inactive historical records.
        rec_a.historical_member_symbol_ids = list(rec_a.member_symbol_ids)
        rec_b.historical_member_symbol_ids = list(rec_b.member_symbol_ids)
        rec_a.member_symbol_ids = []
        rec_b.member_symbol_ids = []
        rec_a.lifecycle_status = "FAMILY_INACTIVE_SUCCESSOR_REUNION"
        rec_b.lifecycle_status = "FAMILY_INACTIVE_SUCCESSOR_REUNION"
        rec_a.inactive_reason = f"Reunited with {source_family_b} into successor {reunited_id}."
        rec_b.inactive_reason = f"Reunited with {source_family_a} into successor {reunited_id}."
        rec_a.lineage_successor_family_ids = [reunited_id]
        rec_b.lineage_successor_family_ids = [reunited_id]
        rec_a.reunion_event_ids.append(evt_id)
        rec_b.reunion_event_ids.append(evt_id)
        rec_a.fission_candidate_counter = 0
        rec_b.fission_candidate_counter = 0
        rec_a.fission_partition_key = None
        rec_b.fission_partition_key = None

        self._families[reunited_id] = reunited

        key = self._pair_key(source_family_a, source_family_b)
        self._pending_reunion.pop(key, None)

        self._reunion_events.append(evt)
