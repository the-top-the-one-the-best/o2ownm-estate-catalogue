from datetime import datetime
from bson import ObjectId
import re
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
