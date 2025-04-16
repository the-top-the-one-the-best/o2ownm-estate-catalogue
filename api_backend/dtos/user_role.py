from marshmallow import EXCLUDE, fields, Schema
from api_backend.dtos.generic import GeneralPagedQueryDto, create_page_result_dto
from api_backend.schemas import ObjectIdHelper, UserPermissionSchema, UserRoleSchema

try:
  fields.ObjectId
except:
  fields.ObjectId = ObjectIdHelper
  
class UpsertUserRoleDto(Schema):
  name = fields.String(missing="", metadata={ "example": "資訊預覽" })
  description = fields.String(missing="", metadata={ "example": "基礎預覽建案、客資，不能進行寫入操作" })
  permissions = fields.Nested(UserPermissionSchema)
  
class QueryUserRoleDto(GeneralPagedQueryDto):
  name = fields.String()
  class Meta:
    unknown = EXCLUDE

PagedUserRoleDto = create_page_result_dto(UserRoleSchema)
