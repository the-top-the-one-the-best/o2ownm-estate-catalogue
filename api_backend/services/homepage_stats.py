import pymongo
from api_backend.utils.mongo_helpers import lookup_collection
from config import Config
from constants import TW_REGIONAL_GROUPS

class HomepageStatsService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.estate_info_collection = self.db.estateinfos
    self.customer_info_collection = self.db.customerinfos

  def get_estate_customer_info_total_count(self):
    return {
      "estate_info_count": self.estate_info_collection.count_documents({}),
      "customer_info_count": self.customer_info_collection.count_documents({}),
    }

  def get_estate_rank_by_customer_info_count(self, query_dto):
    limit = query_dto.get("limit")
    agg_stages = [
      { "$match": { "estate_info_id": { "$ne": None } } },
      { "$group": { "_id": "$estate_info_id", "customer_info_count": { "$sum": 1 } } },
      { "$sort": { "customer_info_count": -1 } },
      { "$limit": limit }
    ]
    lookup_collection(
      agg_stages=agg_stages, 
      target_col=self.estate_info_collection.name,
      local_field="_id",
      as_field="estate_info",
    )
    agg_stages.append({
      "$replaceRoot": {
        "newRoot": {
          "$mergeObjects": [
            "$estate_info",
            { "customer_info_count": "$customer_info_count" },
          ]
        } 
      }
    })
    return list(self.customer_info_collection.aggregate(agg_stages))
  
  def get_region_ranked_by_estate_count(self):
    results = []
    for region in TW_REGIONAL_GROUPS:
      district_estate_count_map = { district: 0 for district in region["districts"] }
      region_estate_aggs = self.estate_info_collection.aggregate([
        { "$match": { "l1_district": { "$in": region["districts"] } } },
        { "$group": { "_id": "$l1_district", "estate_info_count": { "$sum": 1 } } },
      ])
      for agg in region_estate_aggs:
        district_estate_count_map[agg["_id"]] = int(agg["estate_info_count"] or 0)

      results.append({
        "region_name": region["region_name"],
        "restion_stats": [
          { "l1_district": item[0], "estate_info_count": item[1] }
          for item in sorted(
            district_estate_count_map.items(),
            key=lambda item: item[1],
            reverse=True,
          )
        ],
      })
    return results
