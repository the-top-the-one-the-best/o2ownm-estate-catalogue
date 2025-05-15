import flask
from flask_apispec import doc, marshal_with, use_kwargs
from flask_jwt_extended import get_jwt_identity
from api_backend.dtos.customer_tags import (
  PagedCustomerTagDto,
  QueryCustomerTagDto,
  CustomerTagSchema,
  UpsertCustomerTagDto,
)
from api_backend.schemas import CustomerTagSchema
from api_backend.services.customer_tags import CustomerTagsService
from api_backend.utils.auth_utils import check_permission
from api_backend.utils.mongo_helpers import validate_object_id
from config import Config
from constants import APITags, Permission, PermissionTargets

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
customer_tags_service = CustomerTagsService()

@blueprint.route("/_id/<_id>", methods=["GET"])
@doc(
  summary='get customer tag by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.read,
  ),
  tags=[APITags.customer_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.read)
@marshal_with(CustomerTagSchema)
def get_by_id(_id):
  _id = validate_object_id(_id)
  result = customer_tags_service.find_by_id(_id)
  return flask.jsonify(CustomerTagSchema().dump(result))

@blueprint.route("/query", methods=["POST"])
@doc(
  summary='query customer tag by dto, use POST for complicated query body, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.read,
  ),
  tags=[APITags.customer_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.read)
@use_kwargs(QueryCustomerTagDto)
@marshal_with(PagedCustomerTagDto)
def query(**query):
  result = customer_tags_service.query_by_filter(query)
  return flask.jsonify(PagedCustomerTagDto().dump(result))

@blueprint.route("/create", methods=["POST"])
@doc(
  summary='create new customer tag, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.write,
  ),
  tags=[APITags.customer_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.write)
@use_kwargs(UpsertCustomerTagDto)
@marshal_with(CustomerTagSchema)
def create(**kwargs):
  user_id = validate_object_id(get_jwt_identity())
  created = customer_tags_service.create(kwargs, user_id=user_id)
  return flask.jsonify(CustomerTagSchema().dump(created))

@blueprint.route("/_id/<_id>", methods=["PATCH"])
@doc(
  summary='update customer tag by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.write,
  ),
  tags=[APITags.customer_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.write)
@use_kwargs(UpsertCustomerTagDto)
@marshal_with(CustomerTagSchema)
def update_by_id(_id, **kwargs):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  result = customer_tags_service.update_by_id(_id, kwargs, user_id=user_id)
  return flask.jsonify(CustomerTagSchema().dump(result))

@blueprint.route("/_id/<_id>", methods=["DELETE"])
@doc(
  summary='delete customer tag by _id, permission <%s:%s> required' % (
    PermissionTargets.estate_customer_tag,
    Permission.write,
  ),
  tags=[APITags.customer_tags],
  security=[Config.JWT_SECURITY_OPTION],
)
@check_permission(PermissionTargets.estate_customer_tag, Permission.write)
def delete_by_id(_id):
  _id = validate_object_id(_id)
  user_id = validate_object_id(get_jwt_identity())
  customer_tags_service.delete_by_id(_id, user_id=user_id)
  return "", 204
