#!/usr/bin/env python
# coding: utf-8
import json
from sqlite_utils import Database

db_folder = 'db/'
db_file = 'data.db'
db_path = db_folder + db_file
db = Database(db_path)

def db_setup():
    db["friend_list"].create({
        'id':int,
        'name':str,
        'is_deactivated':int,
        'alias':str,
        'photo_url':str
    }, pk="id")

    db["profiles"].create({
        'id':int,
        'name':str,
        'location':str,
        'alias':str,
        'tagline':str,
        'about':str,
        'quotes':str,
        'rel':str,
        'rel_partner':str,
        'details':str,
        'work':str,
        'education':str,
        'family':str,
        'life_events':str,
        'meta_created':str
    }, pk="id")

    db["locations"].create({
        "location":str,
        'coordinates':str
        }, pk="location")

    print('>> Database initialized (%s)' % db_path)

def db_read(table):
    data = []
    for row in db[table].rows:
        data.append(row)
    return data

def db_write(table,data):
    db_table = db[table]
    db_table.insert(data)

def db_update(table,id,data):
    db[table].update(id, data)

def db_to_json(table,filename):
    data = []
    for row in db[table].rows:
        data.append(row)
    json_path = db_folder + filename + '.json'
    with open(json_path, 'w', encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    print('%s extracted to %s' % (table,json_path))

# Initialize database if not yet created
if len(db.table_names()) == 0:
    db_setup()