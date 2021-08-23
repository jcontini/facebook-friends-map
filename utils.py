#!/usr/bin/env python
# coding: utf-8
import os, json
from sqlite_utils import Database
from selenium import webdriver

from webdriver_manager.firefox import GeckoDriverManager
# driver = webdriver.Firefox(executable_path=GeckoDriverManager().install())

# --- Paths ---
db_folder = 'db/'
json_folder = db_folder + 'json/'

if not os.path.exists(json_folder):
    os.makedirs(json_folder)

if not os.path.exists(db_folder):
    os.makedirs(db_folder)

# --- Database ---
db_file = 'data.db'
db_path = db_folder + db_file

db = Database(db_path)

def db_setup():
    db["friend_list"].create({
        'id':int,
    }, pk="id")

    db["profiles"].create({
        'id':int,
        }, pk="id")

    db["locations"].create({
        "location":str
        }, pk="location")

    print('>> Database initialized (%s)' % db_path)

def db_read(table):
    data = []
    for row in db[table].rows:
        data.append(row)
    return data

def db_write(table,data):
    db_table = db[table]
    db_table.insert(data, alter=True)

def db_update(table,id,data):
    db[table].update(id, data, alter=True)

def db_to_json():
    tables = db.table_names()
    for table in tables:
        data = []
        for row in db[table].rows:
            data.append(row)
        json_path = json_folder + table + '.json'
        with open(json_path, 'w+', encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        print('%s extracted to %s' % (table,json_path))

# Initialize database if not yet created
if len(db.table_names()) == 0:
    db_setup()