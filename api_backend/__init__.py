__version__ = "0.1.0"
import bson
import uuid
import flask_cors
import flask_jwt_extended
from flask_apispec import FlaskApiSpec
from collections import namedtuple
from functools import wraps
import pymongo
import werkzeug.exceptions
from flask import Flask, jsonify

def make_app(config, for_manage) -> Flask:
  app = Flask(__name__, static_folder=None)
  def with_app_context_wraps(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
      with app.app_context():
        return function(*args, **kwargs)

    return wrapper
  
  # Custom error handler for semantic errors
  @app.errorhandler(werkzeug.exceptions.UnprocessableEntity)
  def __handle_semantic_error__(error: werkzeug.exceptions.UnprocessableEntity):
    messages = error.data.get('messages', ['Invalid request'])
    return jsonify({'errors': messages}), 400

  @app.errorhandler(werkzeug.exceptions.HTTPException)
  def __handle_exception__(error: werkzeug.exceptions.HTTPException):
    response = jsonify({'message': str(error.description) or str(error)})
    response.status_code = error.code if isinstance(error, werkzeug.exceptions.HTTPException) else 500
    return response

  App = namedtuple("App", ("app", "with_app_context_wraps"))(app, with_app_context_wraps)
  app.config.from_object(config)
  
  # for alembic
  if for_manage:
    return App
  
  # for logout
  jwt_mngr = flask_jwt_extended.JWTManager(app)
  blacklist_jti_collection = pymongo.MongoClient(config.MONGO_MAIN_URI).get_database().blacklistjtis
  @jwt_mngr.token_in_blocklist_loader
  def __check_if_token_revoked__(_, jwt_payload):
    token_in_blacklist = blacklist_jti_collection.find_one({
      "_id": bson.Binary.from_uuid(uuid.UUID(jwt_payload["jti"])),
    })
    return token_in_blacklist is not None

  if config.USE_CORS:
    flask_cors.CORS(app)
  # api
  from . import controllers
  
  url_prefix = app.config["APP_URL_PREFIX"]
  app.register_blueprint(controllers.root.blueprint, url_prefix=f"{url_prefix}")
  app.register_blueprint(controllers.user.blueprint, url_prefix=f"{url_prefix}user")
  app.register_blueprint(controllers.latest_news.blueprint, url_prefix=f"{url_prefix}latest_news")
  app.register_blueprint(controllers.customer_info.blueprint, url_prefix=f"{url_prefix}customer_info")
  app.register_blueprint(controllers.file_ops.blueprint, url_prefix=f"{url_prefix}files")
  
  # for swagger
  docs = FlaskApiSpec(app)
  bp_apispec = app.blueprints.pop("flask-apispec", None)
  bp_apispec.static_url_path = url_prefix + bp_apispec.static_url_path[1:]
  app.register_blueprint(bp_apispec)
  for rule_key, rule in app.url_map._rules_by_endpoint.items():
    if 'flask-apispec.' in rule_key:
      rule.reverse()
      rule.pop()
  
  # Iterate over the rules of the application's url_map
  for rule_key in app.url_map.iter_rules():
    # Check if the rule belongs to the blueprint
    try:
      view_func = app.view_functions[rule_key.endpoint]
      docs.register(view_func, rule_key.endpoint)
    except TypeError:
      pass
    
  api_key_scheme = app.config["JWT_SECURITY_SCHEMA"]
  docs.spec.components.security_scheme("Bearer", api_key_scheme)
  
  # https://github.com/jmcarp/flask-apispec/issues/111#issuecomment-508345581
  for key, value in docs.spec._paths.items():
    docs.spec._paths[key] = {
      inner_key: inner_value
      for inner_key, inner_value in value.items()
      if inner_key != 'options'
    }
            
  return App
  