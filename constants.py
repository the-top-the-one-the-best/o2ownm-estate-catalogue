import enum

class AuthEventTypes(enum.Enum):
  REGISTER = "register"
  VERIFIED_ACCOUNT = "verified"
  CHANGE_PASSWORD = "change-password"
  CHANGE_PROFILE = "change-profile"
  LOGIN = "login"
  TOKEN_EXPIRED = "token-expired"
  LOGOUT = "logout"
  LOGIN_FAILED = "login-failed"
  
def enum_set(c):
  return set(
    value for key, value in c.__dict__.items() if not key.startswith('__')
  )

