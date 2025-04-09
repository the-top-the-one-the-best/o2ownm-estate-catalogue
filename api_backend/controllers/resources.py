import flask
import os
from flask_apispec import doc, marshal_with
from api_backend.schemas import TaiwanAdministrativeDistrictSchema
from constants import APITags

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)

@doc(summary="get TW administrative districts", tags=[APITags.resources])
@blueprint.route("/tw_administrative_districts", methods=["GET"])
@marshal_with(TaiwanAdministrativeDistrictSchema(many=True))
def get_tw_administrative_districts():
  json_path = os.path.join('resources', 'tw_administrative_districts.json')
  return flask.send_file(json_path, mimetype='application/json')
