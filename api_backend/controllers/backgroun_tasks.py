import flask
import werkzeug.exceptions
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.background_tasks import EstateCustomerInfoImportOptionDto, XlsxUploadDto
from api_backend.schemas import SchedulerTaskSchema
from api_backend.services.background_tasks import BackgroundTaskService
from flask_jwt_extended import get_jwt_identity, jwt_required
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
bg_service = BackgroundTaskService()

@blueprint.route('/task_id/<task_id>', methods=['GET'])
@jwt_required()
@doc(
  summary='query upload customer info excel task status',
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with(SchedulerTaskSchema)
def get_task_by_id(task_id):
  target_task = bg_service.get_task_by_id(validate_object_id(task_id))
  return flask.jsonify(SchedulerTaskSchema().dump(target_task))

@blueprint.route('/customer_info_xlsx/estate_info_id/<estate_info_id>', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@doc(
  summary='upload customer info excel for estate by estate id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)

@use_kwargs(EstateCustomerInfoImportOptionDto, location="query")
@use_kwargs(XlsxUploadDto, location="files")
@marshal_with(SchedulerTaskSchema)
def upload_and_process_estate_customer_info_xlsx(estate_info_id, **kwargs):
  user_id = get_jwt_identity()
  auto_create_customer_tags = bool(kwargs.get("auto_create_customer_tags"))
  overwrite_existing_user_by_phone = bool(kwargs.get("overwrite_existing_user_by_phone"))
  timezone_offset = int(kwargs.get("timezone_offset"))
  if 'xlsx' not in flask.request.files:
    raise werkzeug.exceptions.BadRequest('no file found')
  
  xlsx_file = flask.request.files['xlsx']
  new_task = bg_service.upload_and_process_estate_customer_info_xlsx(
    validate_object_id(user_id),
    validate_object_id(estate_info_id),
    xlsx_file,
    auto_create_customer_tags=auto_create_customer_tags,
    overwrite_existing_user_by_phone=overwrite_existing_user_by_phone,
    timezone_offset=timezone_offset,
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))
