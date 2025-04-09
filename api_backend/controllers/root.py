import pytz
import flask
from datetime import datetime
from flask_apispec import doc, marshal_with
from api_backend.schemas import HeartBeatSchema
import constants

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)

@doc(summary="timestamp & heartbeat", tags=[constants.APITags.root])
@blueprint.route("/", methods=["GET"])
@marshal_with(HeartBeatSchema)
def root():
  return flask.jsonify({
    "ts_utc": datetime.now(pytz.UTC).isoformat(timespec="seconds"),
    "version": constants.version,
    "uptime": constants.uptime.isoformat(),
  })

@doc(summary="GAE warmup function", tags=[constants.APITags.root])
@marshal_with("", "204")
@blueprint.route("/_ah/warmup", methods=["GET"])
def get_warmup():
  return "", 204
