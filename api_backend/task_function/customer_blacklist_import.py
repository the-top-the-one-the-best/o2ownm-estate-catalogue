from datetime import datetime, timedelta
import sys
import re
import pymongo
import openpyxl
import pytz
from api_backend.schemas import CustomerBlacklistSchema, CustomerInfoSchema
from api_backend.services.resources import ResourceService
from api_backend.utils.mongo_helpers import validate_object_id
from constants import (
  CUSTOMER_BLACKLIST_XLSX_FIELD_HEADER_MAP,
  CUSTOMER_BLACKLIST_XLSX_HEADER_FIELD_MAP,
  ImportErrorTypes,
  enum_set,
  RoomLayouts,
)
from config import Config
BATCH_SIZE = 200

def create_error_entry(insert_task_id, line_number, field_name, field_header, field_value,error_type):
  result = {
    "insert_task_id": insert_task_id,
    "line_number": line_number,
    "field_name": field_name,
    "field_header": field_header,
    "field_value": field_value,
    "error_type": error_type,
  }
  print('import error', result, file=sys.stderr)
  return result

def import_customer_blacklist_xlsx_to_draft(task, mongo_client=None):
  schema = CustomerBlacklistSchema()
  task_id = task["_id"]
  creator_id = task.get("creator_id")

  # load task parameters
  params = task["params"]
  file_path = params["fs_path"]

  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)

  workbook = openpyxl.load_workbook(file_path)
  worksheet = workbook.active
  headers = [str(cell.value).strip() for cell in worksheet[1]]
  # create headers-fields mapping
  column_map = {
    index: CUSTOMER_BLACKLIST_XLSX_HEADER_FIELD_MAP.get(header, None)
    for index, header in enumerate(headers)
  }
  data_list = []
  error_list = []
  basic_string_fields = {"name", "phone"}
  row_number = 1
  empty_row_count = 0
  for row in worksheet.iter_rows(min_row=2, values_only=True):
    row_error_list = []
    row_number += 1
    data = {
      "created_at": datetime.now(pytz.UTC),
      "creator_id": creator_id,
      "updated_at": datetime.now(pytz.UTC),
      "updater_id": creator_id,
      "insert_task_id": task_id,
    }
    empty_check_row = [field for field in row if field]
    if len(empty_check_row) == 0:
      empty_row_count += 1

    if empty_row_count > 10:
      break
    # for each column (field)
    for index, value in enumerate(row):
      field_name = column_map.get(index)
      if not field_name:
        continue
      if field_name in basic_string_fields:
        data[field_name] = str(value).strip() if value and str(value).strip() else ""

    # check entry has necessary infos
    if data and not data.get("phone"):
      row_error_list.append(
        create_error_entry(
          insert_task_id=task_id,
          line_number=row_number,
          field_name="phone",
          field_header=CUSTOMER_BLACKLIST_XLSX_FIELD_HEADER_MAP.get("phone"),
          field_value="",
          error_type=ImportErrorTypes.missing,
        )
      )
    elif data.get("phone"):
      # check against schema
      error_fields = schema.validate(data)
      __phone_has_error = False
      for error_field in error_fields:
        field_value = str(
          ','.join(str(x) for x in data[error_field])
          if type(data[error_field]) is list else data[error_field]
        )
        row_error_list.append(
          create_error_entry(
            insert_task_id=task_id,
            line_number=row_number,
            field_name=error_field,
            field_header=CUSTOMER_BLACKLIST_XLSX_FIELD_HEADER_MAP.get(error_field),
            field_value=field_value,
            error_type=ImportErrorTypes.format_error,
          )
        )
        # index field must be correct
        if error_field == "phone":
          __phone_has_error = True
        else:
          data[error_field] = None
      error_list += row_error_list
      if not __phone_has_error:
        data["_dirty"] = bool(row_error_list)
        data["phone"] = re.sub(r'\D', '', data["phone"])
        if len(data["phone"]) == 10 and data["phone"].startswith('09'):
          data["phone"] = "886%s" % data["phone"][1:]
        if len(data["phone"]) == 9 and data["phone"][0] == "9":
          data["phone"] = "886%s" % data["phone"]
        data_list.append(data)

  # insert into draft collection
  from api_backend.services.customer_blacklist import CustomerBlacklistService
  customer_blacklist_service = CustomerBlacklistService(mongo_client=mongo_client)
  i = 0
  while True:
    batch = data_list[i:i+BATCH_SIZE]
    if not batch:
      break
    customer_blacklist_service.draft_collection.insert_many(batch)
    i += BATCH_SIZE
  i = 0
  while True:
    batch = error_list[i:i+BATCH_SIZE]
    if not batch:
      break
    customer_blacklist_service.import_error_collection.insert_many(batch)
    i += BATCH_SIZE
  return {
    "message": "%d records processed, %d error found" % (len(data_list), len(error_list)),
    "error_count": len(error_list),
    "import_count": len(data_list),
  }

def import_customer_blacklist_draft_to_live(task, task_collection_name, mongo_client=None):
  # load task parameters
  params = task["params"]
  processed_task_id = validate_object_id(params.get("processed_task_id"))
  allow_minor_format_errors = bool(params.get("allow_minor_format_errors"))
  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)
  from api_backend.services.customer_blacklist import CustomerBlacklistService
  customer_blacklist_service = CustomerBlacklistService(mongo_client=mongo_client)
  insert_count = 0
  # bactch moving from draft to live
  query_filter = { "insert_task_id": processed_task_id }
  if not allow_minor_format_errors:
    query_filter["_dirty"] = { "$ne": True }
  while True:
    batch = list(customer_blacklist_service.draft_collection.find(query_filter).limit(BATCH_SIZE))
    if not batch:
      break
    insert_count += len(batch)
    replace_one_batch = [
      pymongo.ReplaceOne(
        { "phone": elem["phone"] },
        { k: v for k, v in elem.items() if k not in { "_id", "_dirty" } },
        upsert=True,
      ) for elem in batch
    ]
    customer_blacklist_service.collection.bulk_write(replace_one_batch)
    ids = [doc["_id"] for doc in batch]
    customer_blacklist_service.draft_collection.delete_many({"_id": {"$in": ids}})

  # user approve imported data, remove import errors
  customer_blacklist_service.draft_collection.delete_many(
    { "insert_task_id": processed_task_id },
  )
  customer_blacklist_service.import_error_collection.delete_many(
    { "insert_task_id": processed_task_id },
  )
  # update status of import to draft task
  mongo_client.get_database().get_collection(task_collection_name).update_one(
    { "_id": processed_task_id },
    { "$set": { "extra_info.imported_to_live": True } },
  )
  return {
    "message": "%d records inserted" % (insert_count, ),
    "import_count": insert_count,
  }

def discard_customer_blacklist_xlsx_import_draft(task, mongo_client=None):
  # load task parameters
  params = task["params"]
  processed_task_id = validate_object_id(params.get("processed_task_id"))
  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)
  from api_backend.services.customer_blacklist import CustomerBlacklistService
  customer_blacklist_service = CustomerBlacklistService(mongo_client=mongo_client)
  import_error_deletion_result = customer_blacklist_service.import_error_collection.delete_many(
    { "insert_task_id": processed_task_id },
  )
  draft_deletion_result = customer_blacklist_service.draft_collection.delete_many(
    { "insert_task_id": processed_task_id },
  )
  return {
    "message": "%d drafts deleted, %d errors deleted" % (
      draft_deletion_result.deleted_count,
      import_error_deletion_result.deleted_count,
    ),
    "draft_delete_count": draft_deletion_result.deleted_count,
    "error_delete_count": import_error_deletion_result.deleted_count,
  }
