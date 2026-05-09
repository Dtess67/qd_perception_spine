import pytest
from qd_perception_spine.entrenchment_v1 import RollbackEvent, handle_rollback, family_authority, family_suspect
from qd_perception.neutral_family_memory_v1 import NeutralFamilyMemoryV1

def _sig(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

def _spr(v: float) -> dict[str, float]:
    return {"axis_a": v, "axis_b": v, "axis_c": v, "axis_d": v}

def test_single_family_rollback_still_works():
    # Setup
    family_authority.clear()
    family_suspect.clear()
    mem = NeutralFamilyMemoryV1()
    
    # Create a small family (too small for fission)
    for i in range(3):
        mem.join_or_create_family(f"s{i}", _sig(0.1), _spr(0.8), 10)
    
    # Trigger fission check (will be refused due to MIN_MEMBERS_FOR_FISSION=6)
    # We need to set SPLIT_READY status first
    rec = mem.get_family_record("fam_01")
    rec.fracture_status = "FAMILY_SPLIT_READY"
    rec.subgroup_count = 2
    
    mem._check_for_fission("fam_01")
    
    # fam_01 should have authority 1 (not suspect)
    assert family_authority.get("fam_01") == 1

def test_two_family_interaction_includes_both():
    # Setup
    family_authority.clear()
    family_suspect.clear()
    mem = NeutralFamilyMemoryV1()
    
    # Create two families
    for i in range(3):
        mem.join_or_create_family(f"a{i}", _sig(0.1), _spr(0.01), 10) # fam_01
        mem.join_or_create_family(f"b{i}", _sig(0.9), _spr(0.01), 10) # fam_02
        
    # Trigger reunion check (will be refused because they are too far apart)
    mem._check_for_reunion_candidates()
    
    # Both families should have authority 1
    assert family_authority.get("fam_01") == 1
    assert family_authority.get("fam_02") == 1

def test_any_participant_suspect_blocks_all():
    # Setup
    family_authority.clear()
    family_suspect.clear()
    mem = NeutralFamilyMemoryV1()
    
    # Create two families
    for i in range(3):
        mem.join_or_create_family(f"a{i}", _sig(0.1), _spr(0.01), 10) # fam_01
        mem.join_or_create_family(f"b{i}", _sig(0.9), _spr(0.01), 10) # fam_02
        
    # Reset authority to zero (it might have been incremented during family creation if some holds occurred)
    # Actually, join_or_create_family does NOT call handle_rollback.
    # But wait, looking at the logs: "Entrenchment hook triggered: participants=['fam_01', 'fam_02'], authority_incremented=True"
    # This means _check_for_reunion_candidates WAS called during join_or_create_family?
    # No, but maybe some other thing?
    # Wait, I didn't call _check_for_reunion_candidates until AFTER marking suspect.
    # Ah! NeutralFamilyMemoryV1 might call it internally? No, I don't see it in join_or_create_family.
    # WAIT! family_authority.clear() clears the dict.
    
    # Mark one as suspect BEFORE we do anything that might trigger a rollback
    family_suspect["fam_01"] = True
    family_authority["fam_01"] = 0
    family_authority["fam_02"] = 0
    
    # Trigger reunion check (refused)
    mem._check_for_reunion_candidates()
    
    # Authority should NOT be incremented for EITHER family
    assert family_authority.get("fam_01", 0) == 0
    assert family_authority.get("fam_02", 0) == 0
