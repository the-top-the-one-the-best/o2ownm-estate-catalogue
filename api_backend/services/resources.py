import pymongo
from api_backend.schemas import TaiwanAdministrativeDistrictSchema
from api_backend.utils.mongo_helpers import build_mongo_index
from config import Config

class ResourceService():
  __loaded__ = False
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.twdistricts_collection = self.db.twdistricts
    if not ResourceService.__loaded__:
      ResourceService.__loaded__ = True
      for index in (TaiwanAdministrativeDistrictSchema.MongoMeta.index_list):
        build_mongo_index(self.twdistricts_collection, index)

  def get_l1_tw_administrative_districts(self, query_dto):
    l1_district = query_dto.get("l1_district")
    l1_district = l1_district.strip() if l1_district else l1_district
    # TODO: county name alias mapping
    if l1_district:
      l1_district = l1_district.replace("台", "臺")
      return list(self.twdistricts_collection.find({ "name": l1_district }))
    return list(self.twdistricts_collection.find())
  
