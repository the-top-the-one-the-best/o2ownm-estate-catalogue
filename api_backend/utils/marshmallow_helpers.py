from datetime import datetime
from bson import ObjectId
import pytz

def serialize_fields_Field(value):
  if isinstance(value, dict):
    return { k: serialize_fields_Field(v) for k, v in value.items() }
  elif isinstance(value, list):
    return [ serialize_fields_Field(i) for i in value ]
  elif isinstance(value, datetime):
    if not value.tzinfo:
      value = value.replace(tzinfo=pytz.utc)
    return value.isoformat()
  elif isinstance(value, ObjectId):
    return str(value)
  return value
