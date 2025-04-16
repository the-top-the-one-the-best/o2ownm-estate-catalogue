from marshmallow import EXCLUDE, fields, validate
import pytz
from api_backend.dtos.generic import GeneralPagedQueryDto, create_page_result_dto
from api_backend.schemas import SystemLogSchema, ObjectIdHelper
from constants import AuthEventTypes, DataTargets, enum_set

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper
  
class QuerySystemLogDto(GeneralPagedQueryDto):
  user_id = fields.ObjectId()
  target_id = fields.ObjectId()
  target_types = fields.List(fields.String(validate=validate.OneOf(enum_set(DataTargets))))
  event_types = fields.List(fields.String(validate=validate.OneOf(enum_set(AuthEventTypes))))
  start_time = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  end_time = fields.DefaultUTCDateTime(default_timezone=pytz.UTC)
  class Meta:
    unknown = EXCLUDE

PagedSystemLogDto = create_page_result_dto(SystemLogSchema)
