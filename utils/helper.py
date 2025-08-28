from datetime import datetime
import json


import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

def print_serialized(data):
    print(json.dumps(data, indent=2, default=serialize))
    print(f"\n✅ Extracted {len(data)} total entries")

def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
