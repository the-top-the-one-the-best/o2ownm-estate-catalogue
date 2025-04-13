from datetime import datetime
import pytz

version = "250314.1238"
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

class APITags:
  admin = "管理 API"
  customer_info = "建案客資管理-客戶資料"
  estate_info = "建案客資管理-建案資料"
  file_ops = "檔案處裡"
  resources = "資料資源"
  root = "系統 Root"
  user = "帳戶"

class AuthEventTypes:
  admin_create_user = "admin_create_user"
  change_password = "change_password"
  change_password_failed = "change_password_failed"
  change_permission = "change_permission"
  change_profile = "change_profile"
  login = "login"
  login_failed = "login_failed"
  logout = "logout"
  register = "register"
  request_reset_password = "request_reset_password"
  validate_email = "validate_email"

class DataTargets:
  user = "user"
  estate_info = "estate_info"
  customer_info = "customer_info"

class PermissionTargets:
  account = "account"
  homepage = "homepage"
  estate_customer_info = "estate_customer_info"
  estate_customer_tag = "estate_customer_tag"
  user_role_mgmt = "user_role_mgmt"
  user_mgmt = "user_mgmt"
  system_log = "system_log"

class Permission:
  read = "r"
  write = "w"
  full = "rw"
  none = ""

class RoomLayouts:
  layout_1 = "1"
  layout_2 = "2"
  layout_3 = "3"
  layout_4 = "4"
  layout_5_or_more = "5"
  

class TaskTypes:
  import_customer_xlsx = "import_customer_xlsx"
  export_customer_xlsx = "export_customer_xlsx"

class TaskStates:
  pending = "pending"
  running = "running"
  failed = "failed"
  success = "success"

def enum_set(c):
  return set(
    [value for key, value in c.__dict__.items() if not key.startswith("_")]
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
