#!/usr/bin/env python
# coding: utf-8
from sqlite_utils import Database

db_path = 'db/data.db'
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

def db_get(table,pk):
    db[table].get(pk)

def db_write(table,data):
    db_table = db[table]
    db_table.insert(data)

def db_update(table,id,data):
    db[table].update(id, data)

# Initialize database if not yet created
if len(db.table_names()) == 0:
    db_setup()