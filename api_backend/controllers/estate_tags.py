import flask
from flask_apispec import doc, marshal_with, use_kwargs
from flask_jwt_extended import get_jwt_identity, jwt_required
from api_backend.dtos.estate_tags import (
  PagedEstateTagDto,
  QueryEstateTagDto,
  EstateTagSchema,
  UpsertEstateTagDto,
)
from api_backend.schemas import EstateTagSchema
from api_backend.services.estate_tags import EstateTagsService
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
estate_tags_service = EstateTagsService()

@blueprint.route("/_id/<_id>", methods=["GET"])
@doc(
  summary='get estate tag by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.read,
  ),
  tags=[APITags.estate_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.read)
@marshal_with(EstateTagSchema)
def get_by_id(_id):
  _id = validate_object_id(_id)
  result = estate_tags_service.find_by_id(_id)
  return flask.jsonify(EstateTagSchema().dump(result))

@blueprint.route("/query", methods=["POST"])
@doc(
  summary='query estate tag by dto, use POST for complicated query body, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.read,
  ),
  tags=[APITags.estate_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.read)
@use_kwargs(QueryEstateTagDto)
@marshal_with(PagedEstateTagDto)
def query(**query):
  result = estate_tags_service.query_by_filter(query)
  return flask.jsonify(PagedEstateTagDto().dump(result))

@blueprint.route("/create", methods=["POST"])
@doc(
  summary='create new estate tag, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.write,
  ),
  tags=[APITags.estate_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.write)
@use_kwargs(UpsertEstateTagDto)
@marshal_with(EstateTagSchema)
def create(**kwargs):
  user_id = validate_object_id(get_jwt_identity())
  created = estate_tags_service.create(kwargs, user_id=user_id)
  return flask.jsonify(EstateTagSchema().dump(created))

@blueprint.route("/_id/<_id>", methods=["PATCH"])
@doc(
  summary='update estate tag by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.write,
  ),
  tags=[APITags.estate_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.write)
@use_kwargs(UpsertEstateTagDto)
@marshal_with(EstateTagSchema)
def update_by_id(_id, **kwargs):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  result = estate_tags_service.update_by_id(_id, kwargs, user_id=user_id)
  return flask.jsonify(EstateTagSchema().dump(result))

@blueprint.route("/_id/<_id>", methods=["DELETE"])
@doc(
  summary='delete estate tag by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.write,
  ),
  tags=[APITags.estate_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.write)
def delete_by_id(_id):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  estate_tags_service.delete_by_id(_id, user_id=user_id)
  return "", 204
