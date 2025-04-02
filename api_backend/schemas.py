import pytz
from marshmallow import Schema, ValidationError, fields, validate, missing
from bson import ObjectId
from constants import (
  AuthEventTypes,
  DescriptionContentTypes,
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
  event_type = fields.String(validate=validate.OneOf(enum_set(AuthEventTypes)))
  event_details = fields.Dict()
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  
class _ImageSchema(Schema):
  src = fields.Url(required=True)
  href = fields.Url(required=False, allow_none=True, missing=None)

class _DescriptionSchema(Schema):
  type = fields.String(validate=validate.OneOf(enum_set(DescriptionContentTypes)))
  images = fields.Nested(_ImageSchema, many=True, required=False)
  video_url = fields.Url(required=False, allow_none=True, missing=None)
  content = fields.String(required=False)

class _GenericMultimediaBlockSchema(MongoDefaultDocumentSchema):
  title = fields.String(required=True)
  description = fields.Nested(_DescriptionSchema, many=True, required=True)
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)

class LatestNewsSchema(_GenericMultimediaBlockSchema):
  start_time = fields.DefaultUTCDateTime()
  end_time = fields.DefaultUTCDateTime()
  creator_id = fields.ObjectId()
  updater_id = fields.ObjectId()

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

class CustomerInfoSchema(MongoDefaultDocumentSchema):
  # 中文姓名	身分證字號	性別	生日	
  civ_id = fields.String(missing='')
  name_zh = fields.String(missing='')
  gender = fields.Integer(missing=None, allow_none=True)
  birthday = fields.DefaultUTCDateTime(
    default_timezone=pytz.timezone('Asia/Taipei'),
  )

  # 學號	畢業系所	系所代碼	畢業級數
  student_id = fields.String(missing='')
  graduate_dept = fields.String(missing='')
  graduate_dept_code = fields.String(missing='')
  graduate_year = fields.Integer(missing=None)

  # 班別	戶籍電話	戶籍郵遞區號	戶籍地址
  class_type = fields.String(missing='')
  phone_registered = fields.String(missing='')
  zip_registered = fields.String(missing='')
  address_registered = fields.String(missing='')

  # 通訊電話	通訊郵遞區號	通訊地址	個人Email
  phone_contact = fields.String(missing='')
  zip_contact = fields.String(missing='')
  address_contact = fields.String(missing='')
  email = fields.String(validate=lambda x: x == "" or validate.Email())

  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
