import json
import os
from datetime import datetime
from dataclasses import asdict
from typing import List, Any
from qd_perception import __version__

def export_perception_runs(scenario_data: List[dict], filename: str = "runs/perception_demo_audit.json"):
    """
    Exports perception demo scenarios to a structured JSON file with a manifest.
    
    Args:
        scenario_data: List of dictionaries containing scenario run information.
        filename: Path to the output JSON file.
    """
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Create the manifest metadata
    manifest = {
        "module_name": "qd_perception_spine",
        "module_version": __version__,
        "exported_at": datetime.now().isoformat(),
        "scenario_count": len(scenario_data)
    }
    
    # Combine manifest and scenario data
    export_payload = {
        "manifest": manifest,
        "scenarios": scenario_data
    }
    
    # Write to file with clean formatting
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, indent=2)
    
    print(f"\n[Export] Audit data successfully exported to {filename}")

def serialize_result(result: Any) -> dict:
    """
    Recursively converts dataclasses and their nested objects into plain dictionaries.
    This is a helper for JSON serialization of PerceptionResult and its components.
    """
    if hasattr(result, "__dataclass_fields__"):
        return asdict(result)
    return result
