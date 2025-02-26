import pytz
from marshmallow import Schema, ValidationError, fields, validate, missing
from bson import ObjectId
from constants import EventTargetTypes, EventTypes, RealEstateRoomLayoutTypes

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

class EventLogSchema(MongoDefaultDocumentSchema):
  user_id = fields.ObjectId()
  event_type = fields.Enum(EventTypes, by_value=True)
  event_time = fields.AwareDateTime(default_timezone=pytz.UTC)
  target_id = fields.ObjectId()
  target_types = fields.Enum(EventTargetTypes, by_value=True)
  changes = fields.Dict()

class RealEstateTagSchema(MongoDefaultDocumentSchema):
  name = fields.String(required=True)

class CustomerTagSchema(MongoDefaultDocumentSchema):
  name = fields.String(required=True)

class RealEstateSchema(MongoDefaultDocumentSchema):
  name = fields.String(required=True)
  city_county = fields.String(required=True)
  district = fields.String(required=True)
  room_layouts = fields.List(
    fields.Enum(RealEstateRoomLayoutTypes, by_value=True)
  )
  room_sizes = fields.List(fields.List(fields.Number()))
  real_estate_tags = fields.List(fields.ObjectId())
  created_at = fields.AwareDateTime(default_timezone=pytz.UTC)
  updated_at = fields.AwareDateTime(default_timezone=pytz.UTC)

class CustomerInquirySchema(MongoDefaultDocumentSchema):
  real_estate_id = fields.ObjectId()
  name = fields.String(required=True)
  title = fields.String(required=True)
  phone = fields.String(required=True)
  email = fields.Email(allow_none=True)
  room_layout_preferences = fields.List(
    fields.Enum(RealEstateRoomLayoutTypes, by_value=True)
  )
  room_size_preferencs = fields.List(fields.Number())
  file_date = fields.AwareDateTime(default_timezone=pytz.UTC)
  city_county = fields.String(required=True)
  district = fields.String(required=True)
  customer_tags = fields.List(fields.ObjectId())
  created_at = fields.AwareDateTime(default_timezone=pytz.UTC)
  updated_at = fields.AwareDateTime(default_timezone=pytz.UTC)
  