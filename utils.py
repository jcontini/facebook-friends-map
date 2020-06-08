import json
from sqlite_utils import Database

db_path = 'db/data.db'
db = Database(db_path)

schema = {
    'friend_list':{
        'id':0,
        'name':'',
        'is_deactivated':0,
        'alias':'',
        'photo_url':''
    },

    'profiles':{
        'id':0,
        'name':'',
        'alias':'',
        'meta':{},
        'tagline':'',
        'about':'',
        'quotes':'',
        'rel':'',
        'rel_partner':'',
        'details':[],
        'work':[],
        'education':[],
        'family':[],
        'life_events':[]
    },

    'location_coordinates':{
        'name':'',
        'coordinates':''
    },

    'friend_locations':{
        'id':0,
        'name':'',
        'location':''
    }
}

def db_setup():
    for table,columns in schema.items():
        db_table = db[table]
        db_table.insert(columns)
        db_table.delete_where()
    print('>> Database initialized (%s)' % db_path)

def db_read(table):
    data = []
    for row in db[table].rows:
        data.append(row)
    return data

def db_write(table,data):
    db_table = db[table]
    db_table.insert(data)

# Initialize database if not yet created
if len(db.table_names()) == 0:
    db_setup()