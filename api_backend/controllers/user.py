import flask
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.generic import GeneralInsertIdDto
from api_backend.dtos.user import CredentialDto, LoginTokenDto, PublicUserDto, UpdatePasswordDto, UpdateUserDto
from utils import validate_object_id
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity
from api_backend.services.user import UserService
from config import Config

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
user_service = UserService()

@blueprint.route("/login", methods=["POST"])
@doc(
  summary='login with credential',
  tags=['帳戶']
)
@use_kwargs(CredentialDto)
@marshal_with(LoginTokenDto)
def login(**kwargs):
  credential_dto = kwargs
  return flask.jsonify(
    LoginTokenDto().dump(user_service.login(credential_dto))
  )

@blueprint.route("/register", methods=["POST"])
@doc(
  summary='register with credential',
  tags=['帳戶']
)
@use_kwargs(CredentialDto)
@marshal_with(GeneralInsertIdDto)
def register(**kwargs):
  credential_dto = kwargs
  return flask.jsonify(
    GeneralInsertIdDto().dump(user_service.register(credential_dto))
  )

@blueprint.route("/logout", methods=["POST"])
@jwt_required()
@doc(
  summary='logout and disable token',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION],
)
@marshal_with("", "204")
def logout():
  raw_jwt = get_jwt()
  user_service.logout(raw_jwt)
  return '', 204

@blueprint.route("/profile", methods=["GET"])
@jwt_required()
@doc(
  summary='get who I am',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION]
)
@marshal_with(PublicUserDto)
def whoami():
  uid = get_jwt_identity()
  return flask.jsonify(
    PublicUserDto().dump(user_service.get_me(validate_object_id(uid)))
  )

@blueprint.route("/profile", methods=["PATCH"])
@jwt_required()
@doc(
  summary='update profile',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdateUserDto)
@marshal_with(PublicUserDto)
def update_profile(**kwargs):
  uid = get_jwt_identity()
  update_dto = kwargs
  return flask.jsonify(
    PublicUserDto().dump(user_service.update_profile(validate_object_id(uid), update_dto))
  )

@blueprint.route("/password", methods=["PATCH"])
@jwt_required()
@doc(
  sumamry='change password',
  tags=['帳戶'],
  security=[Config.JWT_SECURITY_OPTION]
)
@use_kwargs(UpdatePasswordDto)
def update_password(**kwargs):
  update_pwd_dto = kwargs
  uid = get_jwt_identity()
  user_service.update_password(validate_object_id(uid), update_pwd_dto)
  return "", 204
