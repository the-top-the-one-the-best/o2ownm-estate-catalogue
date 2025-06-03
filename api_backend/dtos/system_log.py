from marshmallow import EXCLUDE, fields, validate
import pytz
from api_backend.dtos.generic import GenericPagedQueryDto, create_page_result_dto
from api_backend.dtos.user import PublicUserDto
from api_backend.schemas import SystemLogSchema, ObjectIdHelper
from constants import AuthEventTypes, DataTargets, enum_set

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper
  
class QuerySystemLogDto(GenericPagedQueryDto):
  user_id = fields.ObjectId()
  email = fields.String()
  target_id = fields.ObjectId()
  target_types = fields.List(fields.String(validate=validate.OneOf(enum_set(DataTargets))))
  event_types = fields.List(fields.String(validate=validate.OneOf(enum_set(AuthEventTypes))))
  start_time = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  end_time = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  class Meta:
    unknown = EXCLUDE

class SystemLogDto(SystemLogSchema):
  user = fields.Nested(PublicUserDto)

PagedSystemLogDto = create_page_result_dto(SystemLogDto)
