from datetime import datetime
import enum
import pytz

version = '250314.1238'
uptime = datetime.now(pytz.UTC)

XLSX_MIME_TYPES = {
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
}
ALLOWED_IMAGE_MIME_TYPES = {
  "image/jpeg": "jpeg",
  "image/png": "png",
  "image/gif": "gif",
  "image/webp": "webp",
}

class DescriptionContentTypes:
  images = "images"
  text = "text"
  video = "video"

class AuthEventTypes:
  register = "register"
  verified = "verified"
  request_reset_password = "request_reset_password"
  admin_create_user = "admin_create_user"
  change_password = "change_password"
  change_profile = "change_profile"
  change_permission = "change_permission"
  login = "login"
  token_expired = "token_expired"
  logout = "logout"
  login_failed = "login_failed"

class TaskStates:
  pending = "pending"
  running = "running"
  failed = "failed"
  success = "success"

class AccessTarget:
  account = 'account'
  homepage = 'homepage'
  estate_customer_info = 'estate_customer_info'
  estate_customer_tag = 'estate_customer_tag'
  user_role_mgmt = 'user_role_mgmt'
  user_mgmt = 'user_mgmt'
  system_log = 'system_log'

class Permission:
  read = "r"
  write = "w"
  full = "rw"
  none = ""

class TaskTypes:
  import_member_xlsx = "import_member_xlsx"

def enum_set(c):
  return set(
    [value for key, value in c.__dict__.items() if not key.startswith('_')]
  )

MEMBER_XLSX_HEADER_MAP = {
  "中文姓名": "name_zh",
  "身分證字號": "civ_id",
  "性別": "gender",
  "生日": "birthday",

  "學號": "student_id",
  "畢業系所": "graduate_dept",
  "系所代碼": "graduate_dept_code",
  "畢業級數": "graduate_year",

  "班別": "class_type",
  "戶籍電話": "phone_registered",
  "戶籍郵遞區號": "zip_registered",
  "戶籍地址": "address_registered",

  "通訊電話": "phone_contact",
  "通訊郵遞區號": "zip_contact",
  "通訊地址": "address_contact",
  "個人Email": "email"
}
