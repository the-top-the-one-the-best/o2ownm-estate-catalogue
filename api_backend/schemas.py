import pytz
from marshmallow import Schema, ValidationError, fields, validate, missing
from bson import ObjectId
from constants import AuthEventTypes

# helper class for ObjectId conversion
class ObjectIdHelper(fields.String):
  def _deserialize(self, value, attr, data, **kwargs):
    try:
      return ObjectId(value)
    except Exception:
      raise ValidationError("invalid ObjectId `%s`" % value)

  def _serialize(self, value, attr, obj):
    if value is None:
      return missing
    return str(value)
  
fields.ObjectId = ObjectIdHelper

class HeartBeatSchema(Schema):
  ts_utc = fields.DateTime()

# base schema for all mongo documents using objectId
class MongoDefaultDocumentSchema(Schema):
  _id = fields.ObjectId()

class UserSchema(MongoDefaultDocumentSchema):
  email = fields.Email(allow_none=True)
  phone = fields.String(validate=validate.Regexp("^09\d{8}$"))
  password = fields.String()
  name = fields.String()
  description = fields.String()
  is_admin = fields.Boolean(default=False)
  is_active = fields.Boolean(default=False)
  created_at = fields.AwareDateTime(default_timezone=pytz.UTC)
  updated_at = fields.AwareDateTime(default_timezone=pytz.UTC)

class AuthLogs(MongoDefaultDocumentSchema):
  user_id = fields.ObjectId()
  event_type = fields.Enum(AuthEventTypes, by_value=True)
  event_details = fields.Dict()
  created_at = fields.AwareDateTime(default_timezone=pytz.UTC)
  