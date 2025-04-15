import base64
import random
import werkzeug.exceptions
from functools import wraps
from flask_jwt_extended import get_jwt, jwt_required
from api_backend.schemas import UserPermissionSchema

# RNG
def generate_salt_string(random_length=24):
  return base64.b64encode(''.join(
    chr(int(random.random() * 128)) for _ in range(random_length)
  ).encode()).decode()

# permission decorator to check if user has the required permission
def admins_only():
  def decorator(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
      if get_jwt().get("is_admin"):
        return func(*args, **kwargs)
      raise werkzeug.exceptions.Forbidden("admin role required")
    return wrapper
  return decorator

def check_permission(permission_target, request_permission):
  def decorator(func):
    @wraps(func)
    @jwt_required()
    def wrapper(*args, **kwargs):
      claims = get_jwt()
      user_permissions = claims.get("permissions", UserPermissionSchema().load({}))

      # check if the user has the required permission
      access_target_permission = user_permissions.get(permission_target, "") or ""
      if claims.get("is_valid") and (
        claims.get("is_admin") or 
        request_permission in access_target_permission
      ):
        return func(*args, **kwargs)
      
      if not claims.get("is_valid"):
        raise werkzeug.exceptions.Forbidden("invalid user")

      raise werkzeug.exceptions.Forbidden(
        "permission <%s:%s> required, but you only have `%s`." % (
          request_permission, permission_target, access_target_permission,
        )
      )
    return wrapper
  return decorator
