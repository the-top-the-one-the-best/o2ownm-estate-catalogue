from datetime import datetime, timedelta
import pymongo
import openpyxl
import pytz
from api_backend.services.resources import ResourceService
from constants import CUSTOMER_XLSX_HEADER_MAP, enum_set, RoomLayouts
from config import Config

def process_customer_xlsx(
    task, 
    check_unique_phone=False, 
    mongo_client=None, 
    member_col_name="customerinfos", 
    customer_tags_col_name="customertags",
    tw_districts_col_name="twdistricts",
  ):
  params = task["params"]
  task_id = task["_id"]
  creator_id = task.get("creator_id")
  file_path = params["fs_path"]
  estate_info_id = params["estate_info_id"]

  if not mongo_client:
    mongo_client = pymongo.MongoClient(Config.MONGO_MAIN_URI)    
  db = mongo_client.get_database()
  member_col = db.get_collection(member_col_name)
  customer_tags_col = db.get_collection(customer_tags_col_name)
  twdistricts_col = db.get_collection(tw_districts_col_name)

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
  __customer_tags = {
    cursor["name"]: cursor["_id"]
    for cursor in customer_tags_col.find({})
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
      elif field_name == "customer_tags":
        found_tags = []
        for tag_name in str(value).split(","):
          tag_name = tag_name.strip()
          found_tag = __customer_tags.get(tag_name)
          if found_tag:
            found_tags.append(found_tag)
        data[field_name] = found_tags
      elif field_name == "info_date":
        if type(value) is datetime:
          data[field_name] = value + timedelta(hours=8)
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
  BATCH_SIZE = 200
  i = 0
  while True:
    batch = data_list[i:i+BATCH_SIZE]
    if not batch:
      break
    if check_unique_phone:
      batch = [
        pymongo.UpdateOne(
          { "estate_info_id": estate_info_id, "phone": elem["phone"] },
          { "$set": elem },
          upsert=True,
        ) for elem in batch
      ]
      member_col.bulk_write(batch)
    else:
      member_col.insert_many(batch)

    i += BATCH_SIZE
  return f"{len(data_list)} records processed"
