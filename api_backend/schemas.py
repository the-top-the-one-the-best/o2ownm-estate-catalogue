import pytz
import re
from datetime import datetime
from marshmallow import (
  Schema,
  ValidationError,
  fields,
  post_dump,
  post_load,
  pre_dump,
  validate,
  missing
)
from bson import ObjectId
from api_backend.utils.marshmallow_helpers import serialize_fields_Field
from constants import (
  AuthEventTypes,
  DataTargets,
  ImportErrorTypes,
  RoomLayouts,
  TaskStates,
  TaskTypes,
  Permission,
  enum_set,
)

# helper class for ObjectId conversion
class ObjectIdHelper(fields.String):
  def __init__(self, *args, **kwargs):
    kwargs.setdefault("metadata", {})
    kwargs["metadata"].setdefault("example", "661ccc3d378a65e30fb784ea")
    super().__init__(*args, **kwargs)
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
    dt = None
    if type(value) is datetime:
      dt = value
    else:
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

class TaiwanCountyZipSchema(Schema):
  name = fields.String()
  zip = fields.String()

class TaiwanAdministrativeDistrictSchema(MongoDefaultDocumentSchema):
  name = fields.String()
  districts = fields.List(fields.Nested(TaiwanCountyZipSchema))
  class MongoMeta:
    index_list = [{ "name": 1, "districts.name": 1 }]

class UserPermissionSchema(Schema):
  account = fields.String(
    default=Permission.full,
    missing=Permission.full,
    validate=validate.OneOf(enum_set(Permission)),
    metadata={ "example": Permission.full },
  )
  homepage = fields.String(
    default=Permission.none, 
    missing=Permission.none, 
    validate=validate.OneOf(enum_set(Permission)),
    metadata={ "example": Permission.read },
  )
  estate_customer_info = fields.String(
    default=Permission.none, 
    missing=Permission.none, 
    validate=validate.OneOf(enum_set(Permission)),
    metadata={ "example": Permission.read },
  )
  estate_customer_tag = fields.String(
    default=Permission.none, 
    missing=Permission.none, 
    validate=validate.OneOf(enum_set(Permission)),
    metadata={ "example": Permission.read },
  )
  user_role_mgmt = fields.String(
    default=Permission.none, 
    missing=Permission.none, 
    validate=validate.OneOf(enum_set(Permission)),
    metadata={ "example": Permission.none },
  )
  user_mgmt = fields.String(
    default=Permission.none, 
    missing=Permission.none, 
    validate=validate.OneOf(enum_set(Permission)),
    metadata={ "example": Permission.none },
  )
  system_log = fields.String(
    default=Permission.none, 
    missing=Permission.none, 
    validate=validate.OneOf(enum_set(Permission)),
    metadata={ "example": Permission.none },
  )

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
  class MongoMeta:
    index_list = [
      { "email": 1, "is_admin": 1, "is_valid": 1, "created_at": 1 }
    ]
  @post_load
  def post_load_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    return data

class SystemLogSchema(MongoDefaultDocumentSchema):
  user_id = fields.ObjectId()
  target_id = fields.ObjectId()
  target_type = fields.String(validate=validate.OneOf(enum_set(DataTargets)))
  event_type = fields.String(validate=validate.OneOf(enum_set(AuthEventTypes)))
  event_details = fields.Field()
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  class MongoMeta:
    index_list = [
      { "user_id": 1, "target_id": 1, "event_type": 1, "target_type": 1, "created_at": -1 },
    ]
  @pre_dump
  def pre_dump_handler(self, data, **kwargs):
    if "event_details" in data:
      data["event_details"] = serialize_fields_Field(data["event_details"])
    return data

class SchedulerTaskSchema(MongoDefaultDocumentSchema):
  task_type = fields.String(
    validate=validate.OneOf(enum_set(TaskTypes)),
    metadata={ "example": TaskTypes.import_customer_xlsx_to_draft }
  )
  state = fields.String(validate=validate.OneOf(enum_set(TaskStates)))
  creator_id = fields.ObjectId()
  trial = fields.Integer(missing=0, default=0)
  params = fields.Field()
  result = fields.Field()
  system_pid = fields.Integer(missing=None)
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  run_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  finished_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  extra_info = fields.Field(
    metadata={
      "example": {
        "import_error_previews_limit": 200,
        "imported_to_live": False,
        "import_error_previews": [
          {
            "line_number" : 2,
            "field_name" : "email",
            "field_header" : "E-Mail",
            "field_value" : "abc#gmail.xom",
            "error_type" : ImportErrorTypes.format_error,
          },
          {
            "line_number" : 3,
            "field_name" : "room_layouts",
            "field_header" : "喜好房型",
            "field_value" : "A, B, 3",
            "error_type" : ImportErrorTypes.invalid_value,
          },
          {
            "line_number" : 3,
            "field_name" : "customer_tags",
            "field_header" : "客戶標籤",
            "field_value" : "一邊玩沙",
            "error_type" : ImportErrorTypes.invalid_value,
          }
        ]
      }
    }
  )
  @pre_dump
  def pre_dump_handler(self, data, **kwargs):
    if "extra_info" in data:
      data["extra_info"] = serialize_fields_Field(data["extra_info"])
    if "params" in data:
      data["params"] = serialize_fields_Field(data["params"])
    if "result" in data:
      data["result"] = serialize_fields_Field(data["result"])
    return data

class EstateTagSchema(MongoDefaultDocumentSchema):
  name = fields.String()
  description = fields.String()
  is_frequently_used = fields.Boolean()
  class MongoMeta:
    index_list = [{ "name": 1, "is_frequently_used": 1 }]

class CustomerTagSchema(MongoDefaultDocumentSchema):
  name = fields.String()
  description = fields.String()
  is_frequently_used = fields.Boolean()
  class MongoMeta:
    index_list = [{ "name": 1, "is_frequently_used": 1 }]

class RoomSizeSchema(Schema):
  size_min = fields.Float(metadata={"example": 25})
  size_max = fields.Float(metadata={"example": 27.5})

class EstateInfoSchema(MongoDefaultDocumentSchema):
  name = fields.String(missing="")
  construction_company = fields.String(missing="")
  address = fields.String()
  l1_district = fields.String(allow_none=True, missing=None, metadata={ "example": "臺南市" })
  l2_district = fields.String(allow_none=True, missing=None, metadata={ "example": "東區" })
  room_layouts = fields.List(
    fields.String(validate=validate.OneOf(enum_set(RoomLayouts))),
    metadata={ "example": list(enum_set(RoomLayouts)) },
  )
  room_sizes = fields.List(fields.Nested(RoomSizeSchema()))
  estate_tags = fields.List(fields.ObjectId())

  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  creator_id = fields.ObjectId()
  updater_id = fields.ObjectId()
  class MongoMeta:
    index_list = [
      { "name": 1, "l1_district": 1, "l2_district": 1, "room_layouts": 1, "updated_at": -1 },
      { "name": 1, "l1_district": 1, "l2_district": 1, "room_sizes.size_min": 1, "updated_at": -1 },
      { "name": 1, "l1_district": 1, "l2_district": 1, "estate_tags": 1, "updated_at": -1 },
    ]
  def __arrange_data__(self, data):
    if type(data.get("room_layouts")) is list:
      data["room_layouts"] = sorted(data["room_layouts"])
    if type(data.get("estate_tags")) is list:
      data["estate_tags"] = sorted(data["estate_tags"])
    return data
  @post_load
  def post_load_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  
class CustomerInfoErrorSchema(MongoDefaultDocumentSchema):
  insert_task_id = fields.ObjectId()
  line_number = fields.Integer(metadata={ "example": 2 })
  field_name = fields.String(metadata={ "example": "email" })
  field_header = fields.String(metadata={ "example": "E-mail" })
  field_value = fields.String(metadata={ "example": "xyz.zbc#gmail.xom" })
  error_type = fields.String(
    validate=validate.OneOf(enum_set(ImportErrorTypes)),
    metadata={ "example": ImportErrorTypes.format_error },
  )
  class MongoMeta:
    index_list = [{ "insert_task_id": 1, "line_number": 1 }]
  
class CustomerInfoSchema(MongoDefaultDocumentSchema):
  estate_info_id = fields.ObjectId()
  name = fields.String(missing="")
  title_pronoun = fields.String(missing="")
  phone = fields.String(
    required=True,
    validate=validate.Regexp("^\+?[\d\s\-().]{7,20}$", error="Invalid phone format."),
  )
  email = fields.String(
    validate=lambda value: validate.Email()(value) if value else True,
    metadata={"example": "alexchiu@bclab.ai"}
  )
  room_layouts = fields.List(
    fields.String(validate=validate.OneOf(enum_set(RoomLayouts))),
    metadata={ "example": [RoomLayouts.layout_2, RoomLayouts.layout_3] },
  )
  room_sizes = fields.List(fields.Nested(RoomSizeSchema()))
  info_date = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  l1_district = fields.String(allow_none=True, missing=None, metadata={ "example": "臺南市" })
  l2_district = fields.String(allow_none=True, missing=None, metadata={ "example": "東區" })
  customer_tags = fields.List(fields.ObjectId())

  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  creator_id = fields.ObjectId()
  updater_id = fields.ObjectId()
  insert_task_id = fields.ObjectId()
  class MongoMeta:
    index_list = [
      { "estate_info_id": 1, "l1_district": 1, "l2_district": 1, "room_layouts": 1, "updated_at": -1 },
      { "estate_info_id": 1, "l1_district": 1, "l2_district": 1, "room_sizes.size_min": 1, "updated_at": -1 },
      { "estate_info_id": 1, "l1_district": 1, "l2_district": 1, "customer_tags": 1, "updated_at": -1 },
      { "insert_task_id": 1 },
    ]
  def __arrange_data__(self, data):
    if type(data.get("phone")) is str:
      data["phone"] = re.sub(r'\D', '', data["phone"])
    if type(data.get("email")) is str:
      data["email"] = data["email"].strip().lower()
    if type(data.get("room_layouts")) is list:
      data["room_layouts"] = sorted(data["room_layouts"])
    if type(data.get("customer_tags")) is list:
      data["customer_tags"] = sorted(data["customer_tags"])
    return data
  @post_load
  def post_load_handler(self, data, **kwargs):
    return self.__arrange_data__(data)
  @post_dump
  def post_dump_handler(self, data, **kwargs):
    return self.__arrange_data__(data)

class CustomerInfoDraftSchema(CustomerInfoSchema):
  _dirty = fields.Boolean(missing=False)

class DistrictInfoSchema(Schema):
  l1_district = fields.String(allow_none=True, missing=None, metadata={ "example": "臺南市" })
  l2_district = fields.String(allow_none=True, missing=None, metadata={ "example": "東區" })

class UserRoleSchema(MongoDefaultDocumentSchema):
  name = fields.String()
  permissions = fields.Nested(UserPermissionSchema)
  description = fields.String()
  created_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  updated_at = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  creator_id = fields.ObjectId()
  updater_id = fields.ObjectId()
