from datetime import datetime
import pytz

version = "20250415.1544"
uptime = datetime.now(pytz.UTC)

XLSX_MIME_TYPES = {
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
}

class APITags:
  admin = "管理 API"
  user_role_mgmt = "角色管理"
  customer_info = "建案客資管理-客戶資料"
  estate_info = "建案客資管理-建案資料"
  customer_tags = "標籤-客戶標籤"
  estate_tags = "標籤-建案標籤"
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

CUSTOMER_XLSX_HEADER_MAP = {
}
