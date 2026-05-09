from dataclasses import dataclass, field
from typing import List, Dict

# Entrenchment Amplification Blocker v0.1:
# Suspect-involved rollbacks do not increase authority.

@dataclass
class RollbackEvent:
    participants: List[str]
    authority_incremented: bool = False

# Global state for testing purposes
family_authority: Dict[str, int] = {}
family_suspect: Dict[str, bool] = {}

def handle_rollback(event: RollbackEvent) -> None:
    """
    Handles a rollback event. If any participant is flagged as a suspect,
    authority increment is skipped for all participants.
    """
    is_suspect_involved = any(family_suspect.get(p, False) for p in event.participants)
    
    if is_suspect_involved:
        # Suspect involved: rollback still occurs and is logged via event,
        # but authority increment is skipped for ALL participating families.
        event.authority_incremented = False
    else:
        # Normal operation: increment authority for ALL participants.
        for participant in event.participants:
            current_auth = family_authority.get(participant, 0)
            family_authority[participant] = current_auth + 1
        event.authority_incremented = True
