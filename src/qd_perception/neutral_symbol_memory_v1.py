from dataclasses import dataclass
from typing import Optional, List, Dict
from .neutral_symbol_identity_v1 import IdentityContractV1, IdentityDecision

@dataclass
class SymbolIdentityRecordV1:
    """
    A persistent record of a neutral structural identity.
    
    Fields:
    - symbol_id: The unique neutral ID (sym_01, sym_02, etc.)
    - primary_region_id: The structural region where this was first/most established.
    - signature_vector: A representative structural signature (averages or representative axes).
    - hit_count: Total number of structural recurrences.
    - stability_history: List of stability scores over time.
    - status: Current identity status (ACTIVE, RETIRED_RESERVED, etc.)
    - last_seen_index: The last event index where this was observed.
    """
    symbol_id: str
    primary_region_id: str
    mint_signature: Dict[str, float]
    current_signature: Dict[str, float]
    mint_spread: Dict[str, float]
    current_spread: Dict[str, float]
    hit_count: int
    stability_history: List[float]
    drift_counter: int
    status: str
    last_seen_index: int

class NeutralSymbolMemoryV1:
    """
    Advanced v1 neutral symbol memory for the QD perception spine.
    
    This memory handles:
    - Storing and retrieving stable structural identities.
    - Comparing new structural regions to prior records.
    - Managing symbol reuse, splitting, and retirement.
    - Following the Identity Contract v1 for all decisions.
    """
    
    def __init__(self, contract: Optional[IdentityContractV1] = None):
        self.contract = contract or IdentityContractV1()
        # Storage for identity records, keyed by symbol_id
        self._records: Dict[str, SymbolIdentityRecordV1] = {}
        # Mapping from region_id to symbol_id for quick lookup
        self._region_to_symbol: Dict[str, str] = {}
        # Counter for generating new neutral symbol IDs
        self._symbol_counter = 0
        
        # Tracks temporary/unstable region hits before they earn a symbol
        self._pending_hits: Dict[str, List[float]] = {}
        
        # Tracks structural traces (accumulated axis sums) of pending regions
        # to ensure trace continuity when a symbol is minted.
        self._pending_signatures: Dict[str, Dict[str, float]] = {}
        
        # Tracks individual axis values for pending regions to calculate 
        # the initial spread/envelope during minting.
        self._pending_observations: Dict[str, List[Dict[str, float]]] = {}
        
    def _calculate_similarity(self, sig1: Dict[str, float], sig2: Dict[str, float]) -> float:
        """Simple deterministic similarity based on axis distance."""
        axes = ["axis_a", "axis_b", "axis_c", "axis_d"]
        total_dist = 0.0
        # If axis is missing from either, treat it as a maximum difference (1.0)
        for axis in axes:
            val1 = sig1.get(axis, 0.0)
            val2 = sig2.get(axis, 0.0)
            total_dist += abs(val1 - val2)
        # Max distance is 4.0 (4 axes * 1.0 distance), normalize to [0, 1] then invert
        return 1.0 - (total_dist / len(axes))

    def process_observation(self, 
                          region_id: str, 
                          stability_score: float, 
                          axes: Dict[str, float],
                          event_index: int) -> IdentityDecision:
        """
        Processes a structural observation through the identity contract.
        
        Decides if this is a reuse, a new symbol, a split, or unstable.
        """
        # 1. Look for an existing symbol for this region
        existing_symbol_id = self._region_to_symbol.get(region_id)
        
        if existing_symbol_id:
            record = self._records[existing_symbol_id]
            
            # Compare against original identity anchor to prevent identity smear
            similarity_to_mint = self._calculate_similarity(axes, record.mint_signature)
            # Similarity to moving average for information
            similarity_to_current = self._calculate_similarity(axes, record.current_signature)
            
            # Persistent drift logic: only trigger if drift is sustained
            is_persistent_drift = False
            if similarity_to_mint < self.contract.DRIFT_SPLIT_THRESHOLD:
                record.drift_counter += 1
                # Threshold for persistence: e.g., 3 consecutive observations
                if record.drift_counter >= 3:
                    is_persistent_drift = True
            else:
                # Reset drift counter if we move back toward the anchor
                record.drift_counter = 0

            # Use contract to evaluate
            decision = self.contract.evaluate(
                region_id=region_id,
                stability_score=stability_score,
                recurrence_count=record.hit_count + 1,
                similarity_to_prior=similarity_to_mint,
                is_persistent_drift=is_persistent_drift
            )
            
            if decision.status == "MATCH_EXISTING":
                record.hit_count += 1
                record.stability_history.append(stability_score)
                record.last_seen_index = event_index
                # Update current_signature toward latest
                for k in ["axis_a", "axis_b", "axis_c", "axis_d"]:
                    obs_val = axes.get(k, 0.0)
                    # Moving average for signature
                    record.current_signature[k] = (record.current_signature[k] * 0.9) + (obs_val * 0.1)
                    # Update current_spread (average absolute deviation)
                    # This tells us how far the latest observation is from the current center
                    deviation = abs(obs_val - record.current_signature[k])
                    record.current_spread[k] = (record.current_spread[k] * 0.9) + (deviation * 0.1)

                decision.symbol_id = existing_symbol_id
                
                # If we are drifting but not yet persistent, add a note to rationale
                if record.drift_counter > 0 and not is_persistent_drift:
                    decision.rationale += f" (Note: observed structural drift counter: {record.drift_counter})"
                
                return decision
            
            if decision.status == "SPLIT":
                # Create a new symbol due to persistent drift
                # Use current spread for the new symbol (simplified)
                new_symbol_id = self._mint_symbol(region_id, axes, [stability_score], event_index, axes_spread=record.current_spread)
                decision.symbol_id = new_symbol_id
                decision.rationale += f" (Split from {existing_symbol_id})"
                return decision
                
            # If it's UNSTABLE or NEW (unexpected here), return it
            return decision

        # 2. No existing symbol for this region, check pending hits
        if region_id not in self._pending_hits:
            self._pending_hits[region_id] = []
            self._pending_signatures[region_id] = {"axis_a": 0.0, "axis_b": 0.0, "axis_c": 0.0, "axis_d": 0.0}
            self._pending_observations[region_id] = []
        
        # Add to pre-symbol history/trace
        self._pending_hits[region_id].append(stability_score)
        self._pending_observations[region_id].append(axes.copy())
        for k in ["axis_a", "axis_b", "axis_c", "axis_d"]:
            val = axes.get(k, 0.0)
            self._pending_signatures[region_id][k] += val
        
        current_hits = len(self._pending_hits[region_id])
        avg_stability = sum(self._pending_hits[region_id]) / current_hits
        
        decision = self.contract.evaluate(
            region_id=region_id,
            stability_score=avg_stability,
            recurrence_count=current_hits
        )
        
        if decision.status == "MATCH_EXISTING":
            # This is the "Earned" case for a new region that just reached the threshold.
            
            # Calculate a representative signature/centroid from pre-mint history 
            # to ensure structural trace continuity.
            traced_axes = {}
            for k, total_val in self._pending_signatures[region_id].items():
                traced_axes[k] = total_val / current_hits
            
            # Calculate the initial structural spread (Average Absolute Deviation)
            # from the pre-mint observations.
            traced_spread = {"axis_a": 0.0, "axis_b": 0.0, "axis_c": 0.0, "axis_d": 0.0}
            for obs in self._pending_observations[region_id]:
                for k in traced_spread:
                    obs_val = obs.get(k, 0.0)
                    traced_spread[k] += abs(obs_val - traced_axes[k])
            
            for k in traced_spread:
                traced_spread[k] /= current_hits

            # Mint the symbol, carrying over full recurrence and the compact trace summary (centroid + spread)
            new_symbol_id = self._mint_symbol(
                region_id, 
                traced_axes, 
                self._pending_hits[region_id], 
                event_index,
                axes_spread=traced_spread
            )
            
            # Clear pre-symbol/pending cache
            del self._pending_hits[region_id]
            del self._pending_signatures[region_id]
            del self._pending_observations[region_id]
            
            decision.symbol_id = new_symbol_id
            decision.status = "NEW" # Re-label as NEW for external caller context
            decision.rationale = (
                f"Region earned persistent identity {new_symbol_id} after {current_hits} hits. "
                f"Initial signature centroid and structural envelope (spread) established from pre-symbol structural trace."
            )
            return decision
        
        return decision

    def _mint_symbol(self, 
                     region_id: str, 
                     axes: Dict[str, float], 
                     stability_history: List[float], 
                     event_index: int,
                     axes_spread: Optional[Dict[str, float]] = None) -> str:
        """Creates a new persistent neutral identity record with established history."""
        self._symbol_counter += 1
        symbol_id = f"sym_{self._symbol_counter:02d}"
        
        # If no spread provided (e.g., first observation in a split), initialize with low spread
        initial_spread = axes_spread.copy() if axes_spread else {"axis_a": 0.0, "axis_b": 0.0, "axis_c": 0.0, "axis_d": 0.0}
        
        record = SymbolIdentityRecordV1(
            symbol_id=symbol_id,
            primary_region_id=region_id,
            mint_signature=axes.copy(),
            current_signature=axes.copy(),
            mint_spread=initial_spread.copy(),
            current_spread=initial_spread.copy(),
            hit_count=len(stability_history),
            stability_history=stability_history.copy(),
            drift_counter=0,
            status="ACTIVE",
            last_seen_index=event_index
        )
        
        self._records[symbol_id] = record
        self._region_to_symbol[region_id] = symbol_id
        return symbol_id

    def get_active_records(self) -> List[SymbolIdentityRecordV1]:
        """Returns all currently active identity records."""
        return [r for r in self._records.values() if r.status == "ACTIVE"]
