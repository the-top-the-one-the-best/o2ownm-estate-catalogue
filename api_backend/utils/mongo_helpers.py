import re
import werkzeug.exceptions
from datetime import datetime
from bson import ObjectId

# validate object id, options: raise or return false
def validate_object_id(_id, raise_exception=True):
  if type(_id) is ObjectId:
    return _id
  pattern = r"^[0-9a-f]{24}$"
  _id = str(_id).lower()
  if _id and re.match(pattern, _id):
    return ObjectId(_id)
  else:
    if raise_exception:
      raise werkzeug.exceptions.BadRequest("%s is not a valid ObjectId" % str(_id))
    return False

# mongo helper
def get_district_query(district_schema):
  result = {}
  if district_schema.get('l1_district'):
    result["l1_district"] = district_schema["l1_district"]
  if district_schema.get('l2_district'):
    result["l2_district"] = district_schema["l2_district"]
  return result

def get_mongo_period(start: datetime, end: datetime):
  interval = {}
  if start:
    interval["$gte"] = start
  if end:
    interval["$lt"] = end
  return interval

def lookup_collection(
    agg_stages: list,
    target_col: str,
    local_field: str,
    as_field: str,
    foreign_field='_id',
    unwind=True,
  ):
  agg_stages.append({
    '$lookup': {
      'from': target_col,
      'localField': local_field,
      'foreignField': foreign_field,
      'as': as_field,
    },
  })
  if unwind:
    agg_stages.append({
      '$unwind': {
        'path':'$%s' % as_field,
        'preserveNullAndEmptyArrays': True,
      }
    })
  return

def generate_index_name(index_descriptor):
  parts = []
  for field, order in index_descriptor.items():
    # Replace '.' with '_'
    safe_field = field.replace('.', '_')
    parts.append(f"{safe_field}_{order}")
  return '__'.join(parts)

def build_mongo_index(collection, index_descriptor):
  index_name = generate_index_name(index_descriptor)
  existing_indexes = collection.index_information()
  if index_name in existing_indexes:
    return
  index_fields = [
    (field, 1 if order >= 0 else -1) 
    for field, order in index_descriptor.items()
  ]
  collection.create_index(index_fields, name=index_name)
  print("Index '%s.%s' created." % (collection.name, index_name))
