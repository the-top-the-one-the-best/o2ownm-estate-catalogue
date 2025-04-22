import flask
import werkzeug.exceptions
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.background_tasks import XlsxUploadDto
from api_backend.schemas import SchedulerTaskSchema
from api_backend.services.background_tasks import BackgroundTaskService
from flask_jwt_extended import get_jwt_identity
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
bg_service = BackgroundTaskService()

@blueprint.route('/customer_info_xlsx/<estate_info_id>', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@doc(
  summary='upload customer info excel for estate by estate id',
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@use_kwargs(XlsxUploadDto, location="files")
@marshal_with(SchedulerTaskSchema)
def upload_and_process_estate_customer_info_xlsx(estate_info_id, **kwargs):
  user_id = get_jwt_identity()
  estate_info_id = validate_object_id(estate_info_id)
  if 'xlsx' not in flask.request.files:
    raise werkzeug.exceptions.BadRequest('no file found')
  xlsx_file = flask.request.files['xlsx']
  new_task = bg_service.upload_and_process_estate_customer_info_xlsx(user_id, estate_info_id, xlsx_file)
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))
