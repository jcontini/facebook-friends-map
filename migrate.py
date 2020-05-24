import json, sqlite3
from sqlite_utils import Database

db_path = 'db/data.db'
db = Database(db_path)

# Data Sources
sources = {
    "friend_list": 'db/index.json',
    "profiles":'db/profiles.json',
    "locations": 'db/friend_locations.json',
    "coordinates": 'db/geo.json'
}

# JSON Reader
def json_open(json_file):
    with open(json_file) as f:
        data = json.load(f)
        return data

# Find JSON object with most root-level parameters
def get_json_schema(json_data):
    json_schema = {}
    num_columns = 0
    for i in json_data:
        if len(i) > num_columns:
            json_schema = i
            num_columns = len(i)
    return json_schema

# JSON to SQLite
def json_to_db(json_data, table):
    #Prep schema
    schema_record = get_json_schema(json_data)
    db_table = db[table]
    db_table.insert(schema_record)
    db_table.delete_where()

    # Insert records
    for i in json_data:
        db_table.insert(i)

# Import sources
for db_name,json_file in sources.items():
    print('Importing %s from %s' %(db_name, json_file))
    data = json_open(json_file)
    json_to_db(data, db_name)