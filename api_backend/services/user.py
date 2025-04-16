import uuid
import bson
import pytz
import pymongo
import werkzeug.exceptions

from bson import ObjectId
from datetime import datetime, timedelta
from api_backend.dtos.user import UpdateUserPermissionDto
from api_backend.schemas import UserPermissionSchema, UserSchema
from api_backend.services.email_notification import EmailService
from api_backend.services.log import LogService
from api_backend.utils.auth_utils import generate_salt_string
from api_backend.utils.mongo_helpers import build_mongo_index
from config import Config
from passlib.hash import pbkdf2_sha256
from constants import DataTargets, AuthEventTypes, Permission
from flask_jwt_extended import (
  create_access_token,
  create_refresh_token, 
)

class UserService():
  __loaded__ = False
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.users
    self.chpwd_request_collection = self.db.passwordresetrequests
    self.blacklist_jti_collection = self.db.blacklistjtis
    self.mail_svc = EmailService()
    self.log_svc = LogService()
    if not UserService.__loaded__:
      UserService.__loaded__ = True
      for index in (UserSchema.MongoMeta.index_list):
        build_mongo_index(self.collection, index)
  
  def __query_by_filter__(self, query_dto):
    match_filter = {}
    page_size = query_dto.get("page_size")
    page_number = query_dto.get("page_number")
    agg_stages = []
    matched_count = None
    if match_filter:
      agg_stages.append({"$match": match_filter})
    # check matched count
    if bool(query_dto.get("count_matched")):
      matched_count = self.collection.count_documents(match_filter)
    agg_stages.append({"$sort": {"is_admin": -1, "is_valid": -1, "_id": 1}})
    agg_stages.append({"$skip": page_size * (page_number - 1)})
    agg_stages.append({"$limit": page_size + 1})
    results = list(self.collection.aggregate(agg_stages))
    for result in results:
      result.update(self.get_permissions_from_user_or_token(result))
    return results[:page_size], bool(len(results) > page_size), matched_count
  
  # controller functions
  def query_by_filter(self, query_dto):
    paged_result, has_more, matched_count = self.__query_by_filter__(query_dto)
    result = {
      "results": paged_result,
      "has_more": has_more,
      "page_size": query_dto.get("page_size"),
      "page_number": query_dto.get("page_number"),
    }
    if not matched_count is None:
      result["matched_count"] = matched_count
    return result

  def get_profile_by_user_id(self, target_user_id):
    target = self.collection.find_one({ "_id": target_user_id })
    if not target:
      raise werkzeug.exceptions.NotFound()
    return target
  
  def update_profile_by_user_id(self, target_user_id, update_dto, run_user_id=None):
    if update_dto.get("email"):
      credential_existed = self.collection.find_one(
        { "email": update_dto["email"], "_id": { "ne": target_user_id } },
        { "_id": 1 },
      )
      if credential_existed:
        raise werkzeug.exceptions.Conflict("email already registered")
    update_dto["updated_at"] = datetime.now(pytz.UTC)
    updated = self.collection.find_one_and_update(
      { "_id": target_user_id },
      { "$set": update_dto },
      return_document=pymongo.ReturnDocument.AFTER,
    )
    if not updated:
      raise werkzeug.exceptions.NotFound()
    self.log_svc.log_auth_events(
      user_id=run_user_id or target_user_id,
      event_type=AuthEventTypes.change_profile,
      target_id=target_user_id,
      target_type=DataTargets.user,
      new_data=update_dto,
    )
    return updated
  
  def update_permissions_by_user_id(self, target_user_id, update_dto, run_user_id=None):
    update_dto["updated_at"] = datetime.now(pytz.UTC)
    target_user = self.collection.find_one({ "_id": target_user_id })
    if not target_user:
      raise werkzeug.exceptions.NotFound()
    target_user.update(update_dto)
    permission_claim = self.get_permissions_from_user_or_token(
      UpdateUserPermissionDto().load(target_user)
    )
    target_user = self.collection.find_one_and_update(
      { "_id": target_user_id },
      { "$set": permission_claim },
      return_document=pymongo.ReturnDocument.AFTER,
    )
    self.log_svc.log_auth_events(
      user_id=run_user_id or target_user_id,
      event_type=AuthEventTypes.change_permission,
      target_id=target_user_id,
      target_type=DataTargets.user,
      new_data=update_dto,
    )
    return target_user
  
  def login(self, credential_dto):
    auth_target = self.collection.find_one({"email": credential_dto["email"]})
    if not auth_target:
      raise werkzeug.exceptions.Forbidden("wrong credential")
    auth_result = pbkdf2_sha256.verify(
      credential_dto["password"],
      auth_target["password"],
    )
    if not auth_result:
      self.log_svc.log_auth_events(auth_target["_id"], AuthEventTypes.login_failed)
      raise werkzeug.exceptions.Forbidden("wrong credential")
    
    self.log_svc.log_auth_events(auth_target["_id"], AuthEventTypes.login)
    return {
      "access_token": create_access_token(
        identity=str(auth_target["_id"]),
        additional_claims=self.get_permissions_from_user_or_token(auth_target),
      ),
      "refresh_token": create_refresh_token(identity=str(auth_target["_id"]))
    }

  def register(self, credential_dto):
    # check create admin logic
    create_admin_flag = False
    if not self.collection.find_one({}):
      create_admin_flag = True
    credential_existed = self.collection.find_one(
      { "email": credential_dto["email"] },
      { "_id": 1 },
    )
    if credential_existed:
      raise werkzeug.exceptions.Conflict("email already registered")
    new_user = UserSchema().load({
      "email": credential_dto["email"],
      "password": pbkdf2_sha256.hash(credential_dto["password"]),
      "is_admin": create_admin_flag,
      "is_valid": create_admin_flag,
    })
    new_user.update(self.get_permissions_from_user_or_token(new_user))
    new_user.update(
      created_at = datetime.now(pytz.UTC),
      updated_at = datetime.now(pytz.UTC),
    )
    new_id = self.collection.insert_one(new_user).inserted_id
    self.log_svc.log_auth_events(
      user_id=new_id,
      event_type=AuthEventTypes.register,
      target_id=new_id,
      target_type=DataTargets.user,
      new_data={"email": credential_dto["email"]},
    )
    return { "_id": str(new_id) }
  
  def refresh_access_token(self, run_user_id, refresh_refresh_token=True):
    auth_target = self.collection.find_one({ "_id": run_user_id })
    result = {
      "access_token": create_access_token(
        identity=str(run_user_id),
        additional_claims=self.get_permissions_from_user_or_token(auth_target),
      ),
    }
    if refresh_refresh_token:
      result["refresh_token"] = create_refresh_token(identity=str(auth_target["_id"]))
    return result
  
  def logout(self, raw_jwt):
    jti = raw_jwt.get("jti")
    user_id = bson.ObjectId(raw_jwt.get(Config.JWT_IDENTITY_CLAIM))
    expiration_timestamp = raw_jwt.get("exp")
    expiration_datetime = datetime.fromtimestamp(expiration_timestamp, tz=pytz.UTC) if expiration_timestamp else None
    _now = datetime.now(pytz.UTC)
    if not expiration_datetime or expiration_datetime > _now:
      self.blacklist_jti_collection.insert_one({
        "_id": bson.Binary.from_uuid(uuid.UUID(jti)),
        "exp_datetime": expiration_datetime,
        "created_at": datetime.now(pytz.UTC),
      })
    self.blacklist_jti_collection.delete_many({"exp_datetime": {"$lt": _now}})
    self.log_svc.log_auth_events(user_id, AuthEventTypes.logout)
    return

  def update_password(self, run_user_id, update_pwd_dto, check_old_pwd=False, validate_user=False):
    new_password = update_pwd_dto.get("new_password")
    set_data = {
      "password": pbkdf2_sha256.hash(new_password),
      "updated_at": datetime.now(pytz.UTC),
    }
    if validate_user:
      set_data["is_valid"] = True

    auth_target = self.collection.find_one({ "_id": run_user_id })
    if not auth_target:
      raise werkzeug.exceptions.NotFound()
    
    if check_old_pwd:
      auth_result = pbkdf2_sha256.verify(update_pwd_dto.get("old_password") or '', auth_target["password"])
      if not auth_result:
        self.log_svc.log_auth_events(auth_target["_id"], AuthEventTypes.change_password_failed)
        raise werkzeug.exceptions.Forbidden("wrong old password")
    
    self.collection.find_one_and_update({ "_id": run_user_id }, { "$set": set_data })
    self.log_svc.log_auth_events(run_user_id, AuthEventTypes.change_password)
    if validate_user:
      self.log_svc.log_auth_events(run_user_id, AuthEventTypes.validate_email)
    return

  def admin_create_user(self, run_user_id, dto, send_email=True):
    credential_existed = self.collection.find_one(
      { "email": dto["email"] },
    )
    if credential_existed:
      raise werkzeug.exceptions.Conflict("email already registered")
    
    salt = generate_salt_string()
    new_user = UserSchema().load(dto)
    new_user.update(self.get_permissions_from_user_or_token(new_user))
    new_user.update(
      password = pbkdf2_sha256.hash(salt),
      created_at = datetime.now(pytz.UTC),
      updated_at = datetime.now(pytz.UTC),
    )
    new_id = self.collection.insert_one(new_user).inserted_id
    self.log_svc.log_auth_events(
      user_id=run_user_id,
      event_type=AuthEventTypes.admin_create_user,
      target_id=new_id,
      target_type=DataTargets.user,
      new_data=dto,
    )
    if send_email:
      self.send_password_reset_email(
        user_id=new_id,
        validate_user=True,
        ttl=Config.CREATE_ACCOUNT_VALID_PERIOD,
      )
    return { "_id": str(new_id) }

  def request_password_reset_email(self, reset_dto):
    self.send_password_reset_email(email=reset_dto["email"])
    return

  def reset_password_with_event_id(self, event_id, reset_dto):
    _now = datetime.now(pytz.UTC)
    self.chpwd_request_collection.delete_many({'expired_at': { '$lt': _now }})
    challenge_entry = self.chpwd_request_collection.find_one({"_id": event_id, 'fulfilled': False })

    if not challenge_entry:
      raise werkzeug.exceptions.NotFound()
    
    salt = reset_dto['salt']
    validate_user = bool(challenge_entry.get('validate_user'))
    if pbkdf2_sha256.verify(salt, challenge_entry['salt_hash']):
      self.update_password(challenge_entry["user_id"], reset_dto, validate_user)
      self.chpwd_request_collection.update_one(
        {"_id": event_id},
        {'$set': {'fulfilled': True}},
      )
    else:
      raise werkzeug.exceptions.Forbidden('wrong reset request or request expired')

  # tool functions
  def get_permissions_from_user_or_token(cls, auth_target):
    claim = {
      "is_admin": bool(auth_target.get("is_admin")),
      "is_valid": bool(auth_target.get("is_valid")),
    }
    if claim["is_admin"]:
      _admin_perm = UserPermissionSchema().dump({})
      for key in _admin_perm:
        _admin_perm[key] = Permission.full
      claim["permissions"] = _admin_perm
    elif claim["is_valid"] and auth_target.get('permissions'):
      claim["permissions"] = UserPermissionSchema().dump(auth_target.get('permissions'))
    else:
      claim["permissions"] = UserPermissionSchema().dump({})
    return claim

  def send_password_reset_email(
      self, 
      email: str = None,
      user_id = None,
      validate_user = False,
      ttl=Config.CHANGE_PWD_VALID_PERIOD,
    ):
    _now = datetime.now(pytz.UTC)
    auth_target = None
    if email:
      auth_target = self.collection.find_one({"email": email})
    elif user_id:
      auth_target = self.collection.find_one({"_id": user_id})
    if not auth_target:
      raise werkzeug.exceptions.NotFound()
    
    # check previous entry, limit # of requests per day
    n_requests_past_24hrs = self.log_svc.count_auth_log_events(
      user_id=auth_target["_id"],
      event_type=AuthEventTypes.request_reset_password,
    )
    
    if n_requests_past_24hrs >= Config.MAX_EMAIL_REQUEST_PER_DAY:
      raise werkzeug.exceptions.TooManyRequests(
        "only %d reset requests per day" % Config.MAX_EMAIL_REQUEST_PER_DAY
      )
    
    self.log_svc.log_auth_events(auth_target["_id"], AuthEventTypes.request_reset_password)

    new_salt = generate_salt_string()
    new_reset_request = {}
    new_reset_request.update(
      user_id = auth_target["_id"],
      email = auth_target["email"],
      salt_hash = pbkdf2_sha256.hash(new_salt),
      created_at = _now,
      expired_at = _now + (ttl or Config.CHANGE_PWD_VALID_PERIOD),
      validate_user = bool(validate_user),
      fulfilled = False,
    )
    event_id = self.chpwd_request_collection.insert_one(new_reset_request).inserted_id
    self.mail_svc.send_email_notify(
      auth_target["email"],
      "reset password",
      self.mail_svc.generate_password_reset_mail_html(event_id, new_salt),
      "html",
      raise_error=True,
    )
    return event_id
