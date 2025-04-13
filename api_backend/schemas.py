import pytz
from marshmallow import Schema, ValidationError, fields, validate, missing
from bson import ObjectId
from constants import (
  AuthEventTypes,
  DescriptionContentTypes,
  RoomLayouts,
  TaskStates,
  TaskTypes,
  Permission,
  enum_set,
)

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

# utc datetime helper
class DefaultUTCDateTime(fields.DateTime):
  def _serialize(self, value, attr, obj, **kwargs):
    if value and value.tzinfo is None:
      value = value.replace(tzinfo=pytz.utc)  # Assign UTC to naive datetimes
    return super()._serialize(value, attr, obj, **kwargs)
  def _deserialize(self, value, attr, data, **kwargs):
    dt = super()._deserialize(value, attr, data, **kwargs)
    if dt.tzinfo is None:  # If incoming datetime has no timezone, assume UTC
      return dt.replace(tzinfo=pytz.utc)
    return dt  # Otherwise, return as-is

fields.DefaultUTCDateTime = DefaultUTCDateTime

class HeartBeatSchema(Schema):
  ts_utc = fields.DefaultUTCDateTime()
  uptime = fields.DefaultUTCDateTime()
  version = fields.String()

class TaiwanAdministrativeDistrictSchema(Schema):
  class TaiwanCountyZipSchema(Schema):
    name = fields.String()
    zip = fields.String()
  name = fields.String()
  districts = fields.List(fields.Nested(TaiwanCountyZipSchema))


# base schema for all mongo documents using objectId
class MongoDefaultDocumentSchema(Schema):
  _id = fields.ObjectId()

class UserPermissionSchema(Schema):
  account = fields.String(default=Permission.full, missing=Permission.full, validate=validate.OneOf(enum_set(Permission)))
  homepage = fields.String(default=Permission.none, missing=Permission.none, validate=validate.OneOf(enum_set(Permission)))
  estate_customer_info = fields.String(default=Permission.none, missing=Permission.none, validate=validate.OneOf(enum_set(Permission)))
  estate_customer_tag = fields.String(default=Permission.none, missing=Permission.none, validate=validate.OneOf(enum_set(Permission)))
  user_role_mgmt = fields.String(default=Permission.none, missing=Permission.none, validate=validate.OneOf(enum_set(Permission)))
  user_mgmt = fields.String(default=Permission.none, missing=Permission.none, validate=validate.OneOf(enum_set(Permission)))
  system_log = fields.String(default=Permission.none, missing=Permission.none, validate=validate.OneOf(enum_set(Permission)))

class PasswordRequestRequestSchema(MongoDefaultDocumentSchema):
  user_id = fields.ObjectId()
  email = fields.Email()
  salt = fields.String()
  created_at = fields.DefaultUTCDateTime()
  expired_at = fields.DefaultUTCDateTime()
  validate_user = fields.Boolean(missing=False, default=False)
  fulfilled = fields.Boolean(missing=False, default=False)

class UserSchema(MongoDefaultDocumentSchema):
  email = fields.Email(allow_none=False, required=True)
  phone = fields.String(validate=validate.Regexp("^09\d{8}$"))
  password = fields.String()
  name = fields.String()
  description = fields.String()
  permissions = fields.Nested(UserPermissionSchema)
  is_admin = fields.Boolean(missing=False)
  is_valid = fields.Boolean(missing=False)
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)

class AuthLogSchema(MongoDefaultDocumentSchema):
  user_id = fields.ObjectId()
  target_id = fields.ObjectId()
  event_type = fields.String(validate=validate.OneOf(enum_set(AuthEventTypes)))
  event_details = fields.Dict()
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  
class _ImageSchema(Schema):
  src = fields.Url(required=True)
  href = fields.Url(required=False, allow_none=True, missing=None)

class SchedulerTaskSchema(MongoDefaultDocumentSchema):
  task_type = fields.String(validate=validate.OneOf(enum_set(TaskTypes)))
  state = fields.String(validate=validate.OneOf(enum_set(TaskStates)))
  creator_id = fields.ObjectId()
  trial = fields.Integer(missing=0, default=0)
  params = fields.Field()
  messages = fields.String()
  system_pid = fields.Integer(missing=None)
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  run_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  finished_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)

class EstateTags(Schema):
  _id = fields.String()
  description = fields.String()

class CustomerTags(Schema):
  _id = fields.String()
  description = fields.String()

class EstateInfoSchema(MongoDefaultDocumentSchema):
  name = fields.String(missing="")
  construction_company = fields.String(missing="")
  address = fields.String()
  l1_district = fields.String(allow_none=True, missing=None)
  l2_district = fields.String(allow_none=True, missing=None)
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  room_sizes = fields.List(fields.List(fields.Float()))
  estate_tags = fields.List(fields.String())
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)

class CustomerInfoSchema(MongoDefaultDocumentSchema):
  estate_info_id = fields.ObjectId()
  name = fields.String(missing="")
  title_pronoun = fields.String(missing="")
  phone = fields.String(missing="")
  email = fields.String(validate=lambda x: x == "" or validate.Email())
  room_layouts = fields.List(fields.String(validate=validate.OneOf(enum_set(RoomLayouts))))
  info_date = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  l1_district = fields.String(allow_none=True, missing=None)
  l2_district = fields.String(allow_none=True, missing=None)
  customer_tags = fields.List(fields.String())
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)

class DistrictInfoSchema(Schema):
  l1_district = fields.String(allow_none=True, missing=None)
  l2_district = fields.String(allow_none=True, missing=None)
