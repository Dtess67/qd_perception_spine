from dataclasses import dataclass
from typing import Optional, List

@dataclass
class SymbolMemoryEntry:
    """
    Represents a stable internal identity for a structural region.
    
    This is a neutral marker (symbol) that is assigned once a specific 
    region_id has shown enough repeated presence and stability.
    """
    symbol_id: str
    region_id: str
    hit_count: int
    stability_score: float
    last_seen_index: int
    rationale: str

class SymbolMemory:
    """
    Manages the accumulation of stable internal identities (symbols) 
    for recurring structural regions.
    """
    
    def __init__(self, hit_threshold: int = 3, stability_threshold: float = 0.7):
        # threshold for how many times we must see a region before it earns a symbol
        self.hit_threshold = hit_threshold
        # threshold for how stable the pattern must be to earn a symbol
        self.stability_threshold = stability_threshold
        
        # storage for memory entries, keyed by region_id
        self._memory: dict[str, SymbolMemoryEntry] = {}
        # counter to generate neutral symbol IDs (sym_01, sym_02, etc.)
        self._symbol_counter = 0

    def observe(self, region_id: str, stability_score: float, event_index: int) -> SymbolMemoryEntry:
        """
        Records an observation of a region and returns the associated memory entry.
        Assigns a new neutral symbol if the region passes the thresholds.
        """
        if region_id in self._memory:
            entry = self._memory[region_id]
            entry.hit_count += 1
            # Simple moving average or update of stability score
            # For v0, we'll just take the latest stability score provided or average it
            entry.stability_score = (entry.stability_score + stability_score) / 2.0
            entry.last_seen_index = event_index
            
            # If it didn't have a symbol but now qualifies, assign one
            if not entry.symbol_id.startswith("sym_"):
                if entry.hit_count >= self.hit_threshold and entry.stability_score >= self.stability_threshold:
                    self._symbol_counter += 1
                    entry.symbol_id = f"sym_{self._symbol_counter:02d}"
                    entry.rationale = f"Earned symbol after {entry.hit_count} hits and stability {entry.stability_score:.2f}"
            else:
                entry.rationale = f"Updated entry (hits: {entry.hit_count}, stability: {entry.stability_score:.2f})"
        else:
            # First time seeing this region
            symbol_id = f"provisional_{region_id}"
            
            # Check if it qualifies immediately (unlikely with hit_threshold > 1)
            if self.hit_threshold <= 1 and stability_score >= self.stability_threshold:
                self._symbol_counter += 1
                symbol_id = f"sym_{self._symbol_counter:02d}"
                rationale = "Earned symbol on first contact (low threshold)."
            else:
                rationale = "New region observed; symbol pending more evidence."
            
            entry = SymbolMemoryEntry(
                symbol_id=symbol_id,
                region_id=region_id,
                hit_count=1,
                stability_score=stability_score,
                last_seen_index=event_index,
                rationale=rationale
            )
            self._memory[region_id] = entry
            
        return entry

    def get_symbol_for_region(self, region_id: str) -> Optional[str]:
        """
        Returns the stable symbol_id for a region if it has one.
        Returns None if no stable symbol has been assigned yet.
        """
        if region_id in self._memory:
            sid = self._memory[region_id].symbol_id
            if sid.startswith("sym_"):
                return sid
        return None

    def entries(self) -> List[SymbolMemoryEntry]:
        """Returns all entries in the symbol memory."""
        return list(self._memory.values())
