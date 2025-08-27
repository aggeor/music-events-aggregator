from datetime import datetime
import json

def print_serialized(data):
    print(f"\n✅ Extracted {len(data)} total entries")
    print(json.dumps(data, indent=2, default=serialize))

def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
