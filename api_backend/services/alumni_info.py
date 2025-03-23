import pymongo
from config import Config

class AlumniInfoService():
  def __init__(
    self,
    mongo_client=pymongo.MongoClient(Config.MONGO_MAIN_URI),
  ):
    self.mongo_client = mongo_client
    self.db = self.mongo_client.get_database()
    self.collection = self.db.alumniinfos
    
    # ensures text index is created only once.
    self.text_index_fields = (
      'graduate_dept', 'graduate_dept_code', 'address_contact',
      'address_registered', 'phone_contact', 'phone_registered',
    )
    return

  def _find_alumni_infos(self, query_dto, find_one=False):
    match_filter = {}
    if query_dto.get('civ_id'):
      match_filter['civ_id'] = str(query_dto['civ_id']).upper()
    if 'gender' in query_dto:
      match_filter['gender'] = query_dto['gender']
    if query_dto.get('student_id'):
      match_filter['student_id'] = query_dto['student_id']
    if query_dto.get('graduate_year'):
      match_filter['graduate_year'] = query_dto['graduate_year']
    if query_dto.get('fulltext_query') and query_dto['fulltext_query'].strip():
      fulltext_query_str = str(query_dto['fulltext_query']).strip().replace(',', ' ').replace(';', ' ').split()
      match_filter['__tokens__'] = {"$all": fulltext_query_str}

    page_size = query_dto.get('page_size') or 20
    page_number = query_dto.get('page_number') or 1
    agg_stages = []
    if match_filter:
      agg_stages.append({'$match': match_filter})

    agg_stages.append({'$project': {'__tokens__': 0}})
    agg_stages.append({'$sort': {'_id': 1}})
    agg_stages.append({'$skip': page_size * (page_number-1)})
    agg_stages.append({'$limit': page_size})

    print (agg_stages)
    results = list(self.collection.aggregate(agg_stages))
    if find_one:
      return results[0] if results else None
    return results

  def query_by_filter(self, query_dto):
    results = {
      "results": self._find_alumni_infos(query_dto),
      "page_size": query_dto.get("page_size"),
      "page_number": query_dto.get("page_number"),
    }
    return results
