from datetime import datetime, timedelta
import pymongo
import openpyxl
import pytz
from api_backend.services.resources import ResourceService
from constants import CUSTOMER_XLSX_HEADER_MAP, enum_set, RoomLayouts
from config import Config

def process_customer_xlsx(
    task, 
    mongo_client=None, 
  ):
  task_id = task["_id"]
  creator_id = task.get("creator_id")

  # load task parameters
  params = task["params"]
  file_path = params["fs_path"]
  estate_info_id = params["estate_info_id"]
  auto_create_customer_tags = bool(params.get("auto_create_customer_tags"))
  overwrite_existing_user_by_phone = bool(params.get("overwrite_existing_user_by_phone"))
  timezone_offset = int(params.get("timezone_offset"))

  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)    

  workbook = openpyxl.load_workbook(file_path)
  worksheet = workbook.active
  headers = [str(cell.value).strip() for cell in worksheet[1]]
  # Ensure all headers exist in the mapping
  column_map = {
    index: CUSTOMER_XLSX_HEADER_MAP.get(header, None)
    for index, header in enumerate(headers)
  }
  data_list = []
  __district_map = ResourceService.DISTRICT_MAP
  __room_layouts = enum_set(RoomLayouts)
  from api_backend.services.customer_tags import CustomerTagsService
  customer_tag_service = CustomerTagsService(mongo_client=mongo_client)
  __customer_tag_name_id_map = {
    cursor["name"]: cursor["_id"]
    for cursor in customer_tag_service.collection.find({})
  }
  basic_string_fields = {"name", "title_pronoun", "phone", "l1_district", "l2_district"}
  for row in worksheet.iter_rows(min_row=2, values_only=True):
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
      elif field_name == "room_layouts":
        data[field_name] = list(
          set(layout.strip() for layout in str(value).split(",")).intersection(__room_layouts)
        )
      elif field_name == "customer_tags" and value:
        found_tag_ids = []
        for tag_name in str(value).split(","):
          tag_name = tag_name.strip()
          found_tag_id = __customer_tag_name_id_map.get(tag_name)
          if found_tag_id:
            found_tag_ids.append(found_tag_id)
          elif auto_create_customer_tags:
            new_tag = customer_tag_service.create({
              "name": tag_name,
              "description": "auto created",
              "is_frequently_used": False,
            })
            __customer_tag_name_id_map[tag_name] = new_tag["_id"]
            found_tag_ids.append(new_tag["_id"])
        data[field_name] = sorted(found_tag_ids)
        
      elif field_name == "info_date":
        if type(value) is datetime:
          data[field_name] = value + timedelta(hours=timezone_offset)
        else:
          data[field_name] = datetime.now(pytz.UTC)
      elif field_name == "room_sizes" and value and value.strip():
        size_ranges = []
        for size_range in str(value).split(","):
          size_range = size_range.strip()
          if "-" in size_range:
            size_min_s, size_max_s = size_range.split("-")
            size_ranges.append({"size_min": float(size_min_s), "size_max": float(size_max_s)})
          else:
            size_ranges.append({"size_min": float(size_range), "size_max": float(size_range)})
        data[field_name] = size_ranges
    
    # check entry has necessary infos
    if data.get("phone") and data.get("name"):
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
        else:
          data["l1_district"] = ""
          data["l2_district"] = ""
      data_list.append(data)

  # Insert into MongoDB
  from api_backend.services.customer_info import CustomerInfoService
  customer_info_service = CustomerInfoService(mongo_client=mongo_client)
  BATCH_SIZE = 200
  i = 0
  while True:
    batch = data_list[i:i+BATCH_SIZE]
    if not batch:
      break
    if overwrite_existing_user_by_phone:
      batch = [
        pymongo.UpdateOne(
          { "estate_info_id": estate_info_id, "phone": elem["phone"] },
          { "$set": elem },
          upsert=True,
        ) for elem in batch
      ]
      customer_info_service.collection.bulk_write(batch)
    else:
      customer_info_service.collection.insert_many(batch)

    i += BATCH_SIZE
  return f"{len(data_list)} records processed"
