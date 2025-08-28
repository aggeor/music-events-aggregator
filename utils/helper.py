from datetime import datetime
import json

def print_serialized(data):
    print(json.dumps(data, indent=2, default=serialize))
    print(f"\n✅ Extracted {len(data)} total entries")

def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
