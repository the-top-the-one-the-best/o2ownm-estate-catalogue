import flask
import werkzeug.exceptions
from flask_apispec import doc, marshal_with, use_kwargs
from api_backend.dtos.file_ops import ImageUploadDto, ImageUploadQueryDto, ImageUploadResultDto, MemberXlsxUploadDto
from api_backend.schemas import SchedulerTaskSchema
from api_backend.services.file_ops import FileOpsService
from flask_jwt_extended import jwt_required, get_jwt_identity
from config import Config
from constants import APITags

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)
fs_ops_svc = FileOpsService()


@blueprint.route('/images/', methods=['POST'])
@jwt_required()
@doc(
  summary='upload image for contents',
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@use_kwargs(ImageUploadDto, location="files")
@use_kwargs(ImageUploadQueryDto, location="query")  # Add query params
@marshal_with(ImageUploadResultDto)
def upload_image(preferred_max_size=None, **kwargs):
  user_id = get_jwt_identity()
  if 'image' not in flask.request.files:
    raise werkzeug.exceptions.BadRequest('no file found')
  image_file = flask.request.files['image']
  url, new_width, new_height = fs_ops_svc.upload_image(user_id, image_file, preferred_max_size)
  return flask.jsonify({
    "url": url,
    "new_width": new_width, 
    "new_height": new_height,
  })


@blueprint.route('/member_xlsx/', methods=['POST'])
@jwt_required()
@doc(
  summary='upload membership excel',
  tags=[APITags.file_ops],
  security=[Config.JWT_SECURITY_OPTION],
)
@use_kwargs(MemberXlsxUploadDto, location="files")
@marshal_with(SchedulerTaskSchema)
def upload_membership_xlsx(**kwargs):
  user_id = get_jwt_identity()
  if 'xlsx' not in flask.request.files:
    raise werkzeug.exceptions.BadRequest('no file found')
  xlsx_file = flask.request.files['xlsx']
  new_task = fs_ops_svc.upload_and_process_member_xlsx(user_id, xlsx_file)
  return flask.jsonify(SchedulerTaskSchema().dump(new_task))
