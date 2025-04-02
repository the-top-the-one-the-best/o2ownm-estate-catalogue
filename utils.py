import re
import hashlib
import base64
import random
import werkzeug.exceptions
from datetime import datetime
from functools import wraps
from bson import ObjectId
from flask_jwt_extended import get_jwt, jwt_required
from api_backend.schemas import UserPermissionSchema

def generate_salt_string(random_length=24):
  return base64.b64encode(''.join(
    chr(int(random.random() * 128)) for _ in range(random_length)
  ).encode()).decode()

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

# used for image file removal while document is updated
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
    for chunk in iter(lambda: f.read(4096), b""):
      hash_sha1.update(chunk)
  return hash_sha1.hexdigest()

# permission decorator to check if user has the required permission
def admins_only():
  def decorator(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
      if get_jwt().get("is_admin"):
        return func(*args, **kwargs)
      raise werkzeug.exceptions.Forbidden("admin role required")
    return wrapper
  return decorator

def check_permission(access_target, request_permission):
  def decorator(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
      claims = get_jwt()
      user_permissions = claims.get("permissions", UserPermissionSchema().load({}))

      # check if the user has the required permission
      access_target_permission = user_permissions.get(access_target, "") or ""
      if claims.get("is_valid") and (
        claims.get("is_admin") or 
        request_permission in access_target_permission
      ):
        return func(*args, **kwargs)
      
      if not claims.get("is_valid"):
        raise werkzeug.exceptions.Forbidden("invalid user")

      raise werkzeug.exceptions.Forbidden(
        "permission <%s:%s> required, but you only have `%s`." % (
          request_permission, access_target, access_target_permission,
        )
      )
    return wrapper
  return decorator
