from datetime import datetime
from bson import ObjectId
import re
import hashlib
import werkzeug.exceptions

# validate object id, options: raise or return false
def validate_object_id(_id_in, raise_exception=True):
  if type(_id_in) is ObjectId:
    return _id_in
  pattern = r"^[0-9a-fA-F]{24}$"
  _id_in = str(_id_in)
  if _id_in and re.match(pattern, _id_in):
    return ObjectId(_id_in)
  else:
    if raise_exception:
      raise werkzeug.exceptions.BadRequest("%s is not a valid ObjectId" % str(_id_in))
    return False

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

def find_resource_recursively(json_object, field_name: str, recur_set=None):
  if recur_set is None:
    recur_set = set()
  if not json_object:
    return recur_set
  elif type(json_object) is list:
    for item in json_object:
      find_resource_recursively(item, field_name, recur_set)
  elif type(json_object) is dict:
    for key, value in json_object.items():
      if key == field_name and type(value) is str:
        recur_set.add(value)
      elif type(value) is list or type(value) is dict:
        find_resource_recursively(value, field_name, recur_set)
  return recur_set

def find_resources_to_remove(old, new, field_name='src'):
  old_set = find_resource_recursively(old, field_name)
  new_set = find_resource_recursively(new, field_name)
  return old_set - new_set

def get_file_sha1(file_path):
  hash_sha1 = hashlib.sha1()
  with open(file_path, "rb") as f:
    for chunk in iter(lambda: f.read(4096), b""):  # Read in 4KB chunks
      hash_sha1.update(chunk)
  return hash_sha1.hexdigest()
