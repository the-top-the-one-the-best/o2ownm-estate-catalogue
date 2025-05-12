from datetime import datetime, timedelta
import sys
import pymongo
import openpyxl
import pytz
from api_backend.schemas import CustomerInfoSchema
from api_backend.services.resources import ResourceService
from api_backend.utils.mongo_helpers import validate_object_id
from constants import (
  CUSTOMER_XLSX_HEADER_FIELD_MAP,
  CUSTOMER_XLSX_FIELD_HEADER_MAP,
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

def import_customer_xlsx_to_draft(task, mongo_client=None):
  schema = CustomerInfoSchema()
  task_id = task["_id"]
  creator_id = task.get("creator_id")

  # load task parameters
  params = task["params"]
  file_path = params["fs_path"]
  estate_info_id = params["estate_info_id"]
  timezone_offset = int(params.get("timezone_offset"))

  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)

  workbook = openpyxl.load_workbook(file_path)
  worksheet = workbook.active
  headers = [str(cell.value).strip() for cell in worksheet[1]]
  # create headers-fields mapping
  column_map = {
    index: CUSTOMER_XLSX_HEADER_FIELD_MAP.get(header, None)
    for index, header in enumerate(headers)
  }
  data_list = []
  error_list = []
  __room_layout_options = enum_set(RoomLayouts)
  __district_map = ResourceService.DISTRICT_MAP
  from api_backend.services.customer_tags import CustomerTagsService
  customer_tag_service = CustomerTagsService(mongo_client=mongo_client)
  __customer_tag_name_id_map = {
    cursor["name"]: cursor["_id"]
    for cursor in customer_tag_service.collection.find({})
  }
  basic_string_fields = {"name", "title_pronoun", "phone", "l1_district", "l2_district"}
  row_number = 1
  for row in worksheet.iter_rows(min_row=2, values_only=True):
    row_error_list = []
    row_number += 1
    data = {
      "estate_info_id": estate_info_id,
      "created_at": datetime.now(pytz.UTC),
      "creator_id": creator_id,
      "updated_at": datetime.now(pytz.UTC),
      "updater_id": creator_id,
      "insert_task_id": task_id,
    }
    for index, value in enumerate(row):
      field_name = column_map.get(index)
      if not field_name:
        continue
      if field_name in basic_string_fields:
        data[field_name] = str(value).strip() if value and str(value).strip() else ""
      elif field_name == "email":
        data[field_name] = str(value).lower().strip() if value and str(value).strip() else ""
      elif field_name == "room_layouts" if value and str(value).strip() else "":
        room_layout_set = set(layout.strip() for layout in str(value).split(","))
        if room_layout_set - __room_layout_options:
          row_error_list.append(
            create_error_entry(
              insert_task_id=task_id,
              line_number=row_number,
              field_name=field_name,
              field_header=CUSTOMER_XLSX_FIELD_HEADER_MAP.get(field_name),
              field_value=", ".join(room_layout_set - __room_layout_options),
              error_type=ImportErrorTypes.invalid_value,
            )
          )
        data[field_name] = list(room_layout_set)
      elif field_name == "customer_tags" and value:
        found_tag_ids = []
        data[field_name] = found_tag_ids
        for tag_name in str(value).split(","):
          tag_name = tag_name.strip()
          found_tag_id = __customer_tag_name_id_map.get(tag_name)
          if found_tag_id:
            found_tag_ids.append(found_tag_id)
          else:
            row_error_list.append(
              create_error_entry(
                insert_task_id=task_id,
                line_number=row_number,
                field_name=field_name,
                field_header=CUSTOMER_XLSX_FIELD_HEADER_MAP.get(field_name),
                field_value=tag_name,
                error_type=ImportErrorTypes.invalid_value,
              )
            )
        found_tag_ids.sort()
        
      elif field_name == "info_date":
        if type(value) is datetime:
          data[field_name] = value + timedelta(hours=timezone_offset)
        else:
          data[field_name] = value
      elif field_name == "room_sizes" and value and value.strip():
        size_ranges = []
        data[field_name] = size_ranges
        for size_range in str(value).split(","):
          try:
            size_range = size_range.strip()
            if "-" in size_range:
              size_min_s, size_max_s = size_range.split("-")
              size_ranges.append({"size_min": float(size_min_s), "size_max": float(size_max_s)})
            else:
              size_ranges.append({"size_min": float(size_range), "size_max": float(size_range)})
          except:
            row_error_list.append(
              create_error_entry(
                insert_task_id=task_id,
                line_number=row_number,
                field_name=field_name,
                field_header=CUSTOMER_XLSX_FIELD_HEADER_MAP.get(field_name),
                field_value=size_range,
                error_type=ImportErrorTypes.format_error,
              )
            )
            
    # check entry has necessary infos
    if data and not data.get("phone"):
      row_error_list.append(
        create_error_entry(
          insert_task_id=task_id,
          line_number=row_number,
          field_name="phone",
          field_header=CUSTOMER_XLSX_FIELD_HEADER_MAP.get("phone"),
          field_value="",
          error_type=ImportErrorTypes.missing,
        )
      )
    elif data.get("phone") and data.get("name"):
      # verify district
      if {"l1_district", "l2_district"}.intersection(data):
        l1_district = data.get("l1_district") or ""
        l2_district = data.get("l2_district") or ""
        l1_district = l1_district.replace("台", "臺")
        l2_district = l2_district.replace("台", "臺")
        target_l1 = __district_map.get(l1_district)
        if target_l1:
          data["l1_district"] = target_l1["name"]
          target_l2 = target_l1["districts"].get(l2_district)
          if target_l2:
            data["l2_district"] = target_l2["name"]
          elif not target_l2 and l2_district:
            row_error_list.append(
              create_error_entry(
                insert_task_id=task_id,
                line_number=row_number,
                field_name="l2_district",
                field_header=CUSTOMER_XLSX_FIELD_HEADER_MAP.get("l2_district"),
                field_value=l2_district,
                error_type=ImportErrorTypes.invalid_value,
              )
            )
        elif not target_l1 and l1_district:
          row_error_list.append(
            create_error_entry(
              insert_task_id=task_id,
              line_number=row_number,
              field_name="l1_district",
              field_header=CUSTOMER_XLSX_FIELD_HEADER_MAP.get("l1_district"),
              field_value=l1_district,
              error_type=ImportErrorTypes.invalid_value,
            )
          )
        else:
          data["l1_district"] = ""
          data["l2_district"] = ""
      
      error_fields = schema.validate(data)
      for error_field in error_fields:
        if error_field in { "room_layouts" }:
          continue
        field_value = str(
          ','.join(str(x) for x in data[error_field]) 
          if type(data[error_field]) is list
          else data[error_field]
        )
        row_error_list.append(
          create_error_entry(
            insert_task_id=task_id,
            line_number=row_number,
            field_name=error_field,
            field_header=CUSTOMER_XLSX_FIELD_HEADER_MAP.get(error_field),
            field_value=field_value,
            error_type=ImportErrorTypes.format_error,
          )
        )
      error_list += row_error_list
      if not row_error_list:
        data_list.append(data)

  # insert into draft collection
  from api_backend.services.customer_info import CustomerInfoService
  customer_info_service = CustomerInfoService(mongo_client=mongo_client)
  i = 0
  while True:
    batch = data_list[i:i+BATCH_SIZE]
    if not batch:
      break
    customer_info_service.draft_collection.insert_many(batch)
    i += BATCH_SIZE
  i = 0
  while True:
    batch = error_list[i:i+BATCH_SIZE]
    if not batch:
      break
    customer_info_service.import_error_collection.insert_many(batch)
    i += BATCH_SIZE
  return {
    "message": "%d records processed, %d error found" % (len(data_list), len(error_list)),
    "error_count": len(error_list),
    "import_count": len(data_list),
  }

def import_customer_draft_to_live(task, task_collection_name, mongo_client=None):
  # load task parameters
  params = task["params"]
  processed_task_id = validate_object_id(params.get("processed_task_id"))
  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)
  from api_backend.services.customer_info import CustomerInfoService
  customer_info_service = CustomerInfoService(mongo_client=mongo_client)
  insert_count = 0
  # bactch moving from draft to live
  while True:
    batch = list(customer_info_service.draft_collection.find(
      { "insert_task_id": processed_task_id },
    ).limit(BATCH_SIZE))
    if not batch:
      break
    insert_count += len(batch)
    replace_one_batch = [
      pymongo.ReplaceOne(
        { "estate_info_id": elem["estate_info_id"], "phone": elem["phone"] },
        { k: v for k, v in elem.items() if k != "_id" },
        upsert=True,
      ) for elem in batch
    ]
    customer_info_service.collection.bulk_write(replace_one_batch)
    ids = [doc["_id"] for doc in batch]
    customer_info_service.draft_collection.delete_many({"_id": {"$in": ids}})

  # user approve imported data, remove import errors
  customer_info_service.import_error_collection.delete_many(
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

def discard_customer_xlsx_import_draft(task, mongo_client=None):
  # load task parameters
  params = task["params"]
  processed_task_id = validate_object_id(params.get("processed_task_id"))
  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)
  from api_backend.services.customer_info import CustomerInfoService
  customer_info_service = CustomerInfoService(mongo_client=mongo_client)
  import_error_deletion_result = customer_info_service.import_error_collection.delete_many(
    { "insert_task_id": processed_task_id },
  )
  draft_deletion_result = customer_info_service.draft_collection.delete_many(
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
