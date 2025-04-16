import flask
from flask_apispec import doc, marshal_with, use_kwargs
from flask_jwt_extended import get_jwt_identity, jwt_required
from api_backend.dtos.system_log import (
  PagedSystemLogDto,
  QuerySystemLogDto,
)
from api_backend.schemas import SystemLogSchema
from api_backend.services.system_log import SystemLogService
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
log_service = SystemLogService()

@blueprint.route("/_id/<_id>", methods=["GET"])
@doc(
  summary='get log by _id, permission <%s:%s> required' % (
    PermissionTargets.system_log,
    Permission.read,
  ),
  tags=[APITags.system_log],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.system_log, Permission.read)
@marshal_with(SystemLogSchema)
def get_by_id(_id):
  _id = validate_object_id(_id)
  result = log_service.find_by_id(_id)
  return flask.jsonify(SystemLogSchema().dump(result))

@blueprint.route("/query", methods=["POST"])
@doc(
  summary='query estate tag by dto, use POST for complicated query body, permission <%s:%s> required' % (
    PermissionTargets.system_log,
    Permission.read,
  ),
  # tags=[APITags.system_log],
  security=[Config.JWT_SECURITY_OPTION],
)
# @check_permission(PermissionTargets.system_log, Permission.read)
@use_kwargs(QuerySystemLogDto)
@marshal_with(PagedSystemLogDto)
def query(**query):
  result = log_service.query_by_filter(query)
  return flask.jsonify(PagedSystemLogDto().dump(result))
