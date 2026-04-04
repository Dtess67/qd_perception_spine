from dataclasses import dataclass
from typing import Optional

@dataclass
class IdentityDecision:
    """
    Represents the outcome of a neutral symbol identity evaluation.
    
    Fields:
    - status: str (NEW, MATCH_EXISTING, UNSTABLE, SPLIT, RETIRED_RESERVED)
    - symbol_id: Optional[str]
    - region_id: str
    - confidence: float (0.0 to 1.0)
    - rationale: str (Structural explanation of the decision)
    """
    status: str
    symbol_id: Optional[str]
    region_id: str
    confidence: float
    rationale: str

class IdentityContractV1:
    """
    Auditable v1 contract for neutral symbol identity in the QD perception spine.
    
    This contract evaluates whether a recurring structural region represents
    the same thing as before, a new thing, or something that has changed enough
    to split into a new identity.
    
    Rule: "If a variable name implies an interpretation the system has not yet earned,
    the name is too early."
    """

    # Thresholds for identity decisions
    MIN_RECURRENCE_FOR_STABLE = 3
    STABILITY_THRESHOLD = 0.7
    DRIFT_SPLIT_THRESHOLD = 0.6  # Similarity below this triggers a split if persistent
    
    def evaluate(self, 
                 region_id: str, 
                 stability_score: float, 
                 recurrence_count: int,
                 similarity_to_prior: float = 1.0,
                 is_persistent_drift: bool = False) -> IdentityDecision:
        """
        Evaluates the identity of a structural region based on structural criteria.
        
        This method classifies the region into a neutral status and provides
        a structural rationale.
        """
        # 1. Check for instability
        if stability_score < self.STABILITY_THRESHOLD:
            return IdentityDecision(
                status="UNSTABLE",
                symbol_id=None,
                region_id=region_id,
                confidence=stability_score,
                rationale=f"Structural stability ({stability_score:.2f}) is below threshold ({self.STABILITY_THRESHOLD})."
            )
            
        # 2. Check for insufficient recurrence
        if recurrence_count < self.MIN_RECURRENCE_FOR_STABLE:
            return IdentityDecision(
                status="NEW",
                symbol_id=None,
                region_id=region_id,
                confidence=stability_score * (recurrence_count / self.MIN_RECURRENCE_FOR_STABLE),
                rationale=f"Insufficient structural recurrence ({recurrence_count}/{self.MIN_RECURRENCE_FOR_STABLE}) to earn stable identity."
            )
        
        # 3. Success: Match existing or earn new
        # Similarity check for split/drift
        # If similarity is low and it's not just noise (persistent drift), suggest a split.
        if similarity_to_prior < self.DRIFT_SPLIT_THRESHOLD and is_persistent_drift:
            return IdentityDecision(
                status="SPLIT",
                symbol_id=None, # Caller should mint a new ID
                region_id=region_id,
                confidence=1.0 - similarity_to_prior,
                rationale=f"Structural signature similarity ({similarity_to_prior:.2f}) indicates persistent drift below split threshold ({self.DRIFT_SPLIT_THRESHOLD})."
            )
            
        return IdentityDecision(
            status="MATCH_EXISTING",
            symbol_id=None, # Caller fills this in from memory
            region_id=region_id,
            confidence=similarity_to_prior,
            rationale=f"Stable structural recurrence ({recurrence_count}) with high similarity ({similarity_to_prior:.2f})."
        )
