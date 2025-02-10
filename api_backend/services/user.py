import uuid
import bson
import pytz
import pymongo
import werkzeug.exceptions

from bson import ObjectId
from datetime import datetime
from api_backend.dtos import CredentialDto
from config import Config
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import (
  create_access_token,
  create_refresh_token, 
)

class UserService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.users
    self.blacklist_jti_collection = self.db.blacklistjtis
    return
  
  def get_me(self, uid: ObjectId):
    target = self.collection.find_one({ "_id": uid })
    if not target:
      raise werkzeug.exceptions.NotFound()
    return target
  
  def update_profile(self, uid: ObjectId, update_dto):
    if update_dto.get("email"):
      credential_existed = self.collection.find_one(
        { "email": update_dto["email"], "_id": { "ne": uid } },
        { "_id": 1 },
      )
      if credential_existed:
        raise werkzeug.exceptions.Conflict("email already registered")
    
    update_dto["updated_at"] = datetime.now(pytz.UTC)
    updated = self.collection.find_one_and_update(
      { "_id": uid },
      { "$set": update_dto },
      return_document=pymongo.ReturnDocument.AFTER,
    )
    if not updated:
      raise werkzeug.exceptions.NotFound()
    return updated
  
  def login(self, credential_dto):
    error = CredentialDto().validate(credential_dto)
    if error:
      raise werkzeug.exceptions.BadRequest()
    auth_target = self.collection.find_one({"email": credential_dto["email"]})
    if not auth_target:
      raise werkzeug.exceptions.Forbidden("wrong credential")
    auth_result = pbkdf2_sha256.verify(
      credential_dto["password"],
      auth_target["password"],
    )
    if not auth_result:
      raise werkzeug.exceptions.Forbidden("wrong credential")
    return {
      "access_token": create_access_token(
        identity=str(auth_target["_id"]),
        additional_claims={"is_admin": bool(auth_target.get("is_admin"))},
      ),
      "refresh_token": create_refresh_token(identity=str(auth_target["_id"]))
    }

  def register(self, credential_dto):
    credential_existed = self.collection.find_one(
      { "email": credential_dto["email"] },
      { "_id": 1 },
    )
    if credential_existed:
      raise werkzeug.exceptions.Conflict("email already registered")

    new_user = {
      "email": credential_dto["email"],
      "password": pbkdf2_sha256.hash(credential_dto["password"]),
      "is_admin": False,
      "is_valid": False,
      "created_at": datetime.now(pytz.UTC),
      "updated_at": datetime.now(pytz.UTC),
    }
    new_id = self.collection.insert_one(new_user).inserted_id
    return { "_id": str(new_id) }
  
  def logout(self, raw_jwt):
    jti = raw_jwt.get("jti")
    expiration_timestamp = raw_jwt.get("exp")
    expiration_datetime = datetime.utcfromtimestamp(expiration_timestamp) if expiration_timestamp else None
    if expiration_datetime:
      expiration_datetime = pytz.UTC.localize(expiration_datetime)
    _now = datetime.now(pytz.UTC)
    if not expiration_datetime or expiration_datetime > _now:
      self.blacklist_jti_collection.insert_one({
        "_id": bson.Binary.from_uuid(uuid.UUID(jti)),
        "exp_datetime": expiration_datetime,
        "created_at": datetime.now(pytz.UTC),
      })
    self.blacklist_jti_collection.delete_many({"exp_datetime": {"$lt": _now}})
    return

  def update_password(self, uid: ObjectId, update_pwd_dto):
    new_password = update_pwd_dto.get("new_password")
    target = self.collection.find_one_and_update(
      { "_id": uid },
      { 
        "$set": {
          "password": pbkdf2_sha256.hash(new_password),
          "updated_at": datetime.now(pytz.UTC),
        }
      }
    )
    if not target:
      raise werkzeug.exceptions.NotFound()
    return
