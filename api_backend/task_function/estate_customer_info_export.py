import pymongo
from api_backend.services.customer_blacklist import CustomerBlacklistService
from api_backend.services.customer_info import CustomerInfoService
from config import Config
from openpyxl import Workbook

from constants import CUSTOMER_XLSX_EXPORT_FIELD_HEADER_MAP
BATCH_SIZE = 200

def export_customer_xlsx(task, mongo_client=None):
  # load task parameters
  params = task["params"]
  file_path = params["fs_path"]
  filter = params["filter"]
  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)

  customer_info_service = CustomerInfoService(mongo_client=mongo_client)
  customer_blacklist_service = CustomerBlacklistService(mongo_client=mongo_client)
  blacklist_phones = set(
    entry.get("phone")
    for entry in customer_blacklist_service.collection.find({})
  )
  export_cursor = customer_info_service.query_export_cursor(filter)

  # start writing
  wb = Workbook()
  ws = wb.active
  ws.title = "Contacts"
  ws.append(list(CUSTOMER_XLSX_EXPORT_FIELD_HEADER_MAP.values()))
  
  i = 0
  for entry in export_cursor:
    i += 1
    if entry.get("phone") not in blacklist_phones:
      ws.append([entry[field] for field in CUSTOMER_XLSX_EXPORT_FIELD_HEADER_MAP])

  # Save the workbook
  wb.save(file_path)
  return {
    "message": "%d records exported" % (i,),
    "export_count": i,
  }
