import enum

class EventTypes(str, enum.Enum):
  REGISTER = "register"
  VERIFIED_ACCOUNT = "verified"
  CHANGE_PASSWORD = "change-password"
    
  LOGIN = "login"
  LOGIN_EXPIRED = "login-expired"
  LOGIN_FAILED = "login-failed"
  LOGOUT = "logout"
  
  CREATE_DATA = "create-data"
  READ_DATA = "read-data"
  UPDATE_DATA = "update-data"
  DELETE_DATA = "delete-data"
  
class EventTargetTypes(str, enum.Enum):
  PROFILE = "profile"
  
  REAL_ESTATE = "real-estate"
  CUSTOMER_INQUIRY = "customer-inquiry"
  REAL_ESTATE_TAG = "real-estate-tag"
  CUSTOMER_TAG = "customer-tag"
  
class RealEstateRoomLayoutTypes(str, enum.Enum):
  LAYOUT_1 = "1"
  LAYOUT_2 = "2"
  LAYOUT_3 = "3"
  LAYOUT_4 = "4"
  LAYOUT_5 = "5+"
  
def enum_set(c):
  return set(
    value for key, value in c.__dict__.items() if not key.startswith('__')
  )

