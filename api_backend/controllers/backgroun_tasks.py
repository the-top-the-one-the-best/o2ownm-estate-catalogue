import flask
import werkzeug.exceptions
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.background_tasks import (
  ApproveDraftImportOptionsDto,
  EstateCustomerInfoExportOptionDto,
  EstateCustomerInfoImportOptionDto,
  XlsxUploadDto,
)
from api_backend.dtos.customer_info import FilterCustomerInfoDto
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
  summary='query task status',
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with(SchedulerTaskSchema)
def get_task_by_id(task_id):
  target_task = bg_service.get_task_by_id(validate_object_id(task_id))
  return flask.jsonify(SchedulerTaskSchema().dump(target_task))

@blueprint.route('/customer_info_xlsx/draft/estate_info_id/<estate_info_id>', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@doc(
  summary='upload customer info excel by estate id into draft, permission <%s:%s> required' % (
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
  timezone_offset = int(kwargs.get("timezone_offset"))
  if 'xlsx' not in flask.request.files:
    raise werkzeug.exceptions.BadRequest('no file found')
  
  xlsx_file = flask.request.files['xlsx']
  new_task = bg_service.import_customer_xlsx_to_draft(
    validate_object_id(user_id),
    validate_object_id(estate_info_id),
    xlsx_file,
    timezone_offset=timezone_offset,
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))

@blueprint.route('/customer_info_xlsx/approve/<draft_import_task_id>', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@use_kwargs(ApproveDraftImportOptionsDto)
@doc(
  summary='approve import task by moving customer info from draft to live collection, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with(SchedulerTaskSchema)
def approve_customer_info_import_task_by_id(draft_import_task_id, **kwargs):
  user_id = get_jwt_identity()
  allow_minor_format_errors = bool(kwargs.get("allow_minor_format_errors"))
  new_task = bg_service.approve_customer_info_import_task_by_id(
    validate_object_id(user_id),
    validate_object_id(draft_import_task_id),
    allow_minor_format_errors=allow_minor_format_errors,
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))

@blueprint.route('/customer_info_xlsx/reject/<draft_import_task_id>', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@doc(
  summary='reject import task, delete drafts and import errors, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with(SchedulerTaskSchema)
def reject_customer_info_import_task_by_id(draft_import_task_id):
  user_id = get_jwt_identity()
  new_task = bg_service.reject_customer_info_import_task_by_id(
    validate_object_id(user_id),
    validate_object_id(draft_import_task_id),
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))

@blueprint.route('/customer_info_xlsx/export_by_filter', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.read)
@doc(
  summary='export customer info, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.read,
  ),
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@use_kwargs(EstateCustomerInfoExportOptionDto, location="query")
@use_kwargs(FilterCustomerInfoDto)
@marshal_with(SchedulerTaskSchema)
def export_customer_info_by_filter(**kwargs):
  user_id = get_jwt_identity()
  query_dto = kwargs
  new_task = bg_service.export_customer_info_by_filter(
    validate_object_id(user_id),
    query_dto,
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))

# blacklist
@blueprint.route('/customer_blacklist_xlsx/draft', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@doc(
  summary='upload customer blacklist excel by estate id into draft, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@use_kwargs(XlsxUploadDto, location="files")
@marshal_with(SchedulerTaskSchema)
def upload_and_process_customer_blacklist_xlsx(**kwargs):
  user_id = get_jwt_identity()
  if 'xlsx' not in flask.request.files:
    raise werkzeug.exceptions.BadRequest('no file found')
  
  xlsx_file = flask.request.files['xlsx']
  new_task = bg_service.import_customer_blacklist_to_draft(
    validate_object_id(user_id),
    xlsx_file,
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))

@blueprint.route('/customer_blacklist_xlsx/approve/<draft_import_task_id>', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@use_kwargs(ApproveDraftImportOptionsDto)
@doc(
  summary='approve import task by moving customer blacklist from draft to live collection, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with(SchedulerTaskSchema)
def approve_customer_blacklist_import_task_by_id(draft_import_task_id, **kwargs):
  user_id = get_jwt_identity()
  allow_minor_format_errors = bool(kwargs.get("allow_minor_format_errors"))
  new_task = bg_service.approve_customer_blacklist_import_task_by_id(
    validate_object_id(user_id),
    validate_object_id(draft_import_task_id),
    allow_minor_format_errors=allow_minor_format_errors,
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))

@blueprint.route('/customer_blacklist_xlsx/reject/<draft_import_task_id>', methods=['POST'])
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@doc(
  summary='reject import task, delete drafts and import errors, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_info,
    Permission.write,
  ),
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with(SchedulerTaskSchema)
def reject_customer_blacklist_import_task_by_id(draft_import_task_id):
  user_id = get_jwt_identity()
  new_task = bg_service.reject_customer_blacklist_import_task_by_id(
    validate_object_id(user_id),
    validate_object_id(draft_import_task_id),
  )
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))
