import flask
from flask_apispec import doc, marshal_with, use_kwargs
from flask_jwt_extended import get_jwt_identity, jwt_required
from api_backend.dtos.estate_info import PagedEstateInfoDto, QueryEstateInfoDto, UpsertEstateInfoDto, PublicEstateInfoDto
from api_backend.services.estate_info import EstateInfoService
from config import Config
from constants import APITags, Permission, PermissionTargets
from utils import check_permission, validate_object_id

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
estate_info_service = EstateInfoService()

@blueprint.route("/create", methods=["POST"])
@doc(
  summary='create new estate info',
  tags=[APITags.estate_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@check_permission(PermissionTargets.estate_customer_info, Permission.write)
@use_kwargs(UpsertEstateInfoDto)
@marshal_with(PublicEstateInfoDto)
def create(**kwargs):
  uid = get_jwt_identity()
  create_dto = kwargs
  created = estate_info_service.create(validate_object_id(uid), create_dto)
  return flask.jsonify(PublicEstateInfoDto().dump(created))


@blueprint.route("/_id/<_id>", methods=["GET"])
@doc(
  summary='get find estate info by _id',
  tags=[APITags.estate_info],
  security=[Config.JWT_SECURITY_OPTION],
)
@jwt_required()
@check_permission(PermissionTargets.estate_customer_info, Permission.read)
@marshal_with(PublicEstateInfoDto)
def get_by_id(_id):
  _id = validate_object_id(_id)
  result = estate_info_service.find_by_id(_id)
  return flask.jsonify(PublicEstateInfoDto().dump(result))
