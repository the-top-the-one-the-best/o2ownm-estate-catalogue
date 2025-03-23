import pytz
import flask
from datetime import datetime
from flask_apispec import doc, marshal_with
from api_backend.schemas import HeartBeatSchema
import constants

name = __name__.replace(".", "_")
blueprint = flask.Blueprint(name, __name__)

@doc(summary="timestamp and healthcheck", tags=["root"])
@blueprint.route("/", methods=["GET"])
@marshal_with(HeartBeatSchema)
def root():
  return flask.jsonify({
    "ts_utc": datetime.now(pytz.UTC).isoformat(timespec="seconds"),
    "version": constants.version,
    "uptime": constants.uptime.isoformat(),
  })

@doc(summary="gae warmup function", tags=["root"])
@marshal_with("", "204")
@blueprint.route("/_ah/warmup", methods=["GET"])
def _get_warmup():
  return "", 204
