# -*- coding: utf-8 -*-
"""
Created on Thu Dec 04 14:27:01 2014

@author: Michael K. Maddeford
"""

from bottle import route, run, debug, static_file, url, view
import pyodbc
from os import getenv
from datetime import datetime, timedelta
from natsort import natsorted
from itertools import groupby
import gdata.docs.client
import re

ROW_RE = re.compile('<span>(.*?)</span>')
TEMP_FILE = 'transitory.txt'
DOCUMENT_NAME = 'SSA Doc' # google docs name
username = getenv('GOOG_UID') # google/gmail login id
passwd = getenv('GOOG_PWD') # google/gmail login password

server = getenv('SSA_SERVER')
db = getenv('SSA_DATABASE')
uid = getenv('SSA_UID')
pwd = getenv('SSA_PWD')

connection_string = 'DRIVER={{SQL Server}};SERVER={0};DATABASE={1};UID={2};'\
                    'PWD={3}'.format(server, db, uid, pwd)

conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

def get_time_int(time):
    """Return 15-min time interval as a string tuple.
    
    Keyword arguments:
    time -- the time to convert into a fifteen minute interval
    
    Return the fifteen minute interval into which the given time falls.  For 
    example, if current time is 12:06:67, return (12:00:00, 12:14:59.999)
    """

    minutes = time.minute / 15 * 15

    datehour = time.strftime('%Y-%m-%d %H:')
    time_floor = datehour + str(minutes) + ':00'
    time_ceiling = datehour + str(minutes + 14) + ':59.999'

    return (time_floor, time_ceiling)

def load_docs():
    client = gdata.docs.client.DocsClient(source='drive_test')
    client.ClientLogin(username, passwd, client.source)
    return client

def retrieve_doc():
    client = load_docs()
    doc_list = client.get_resources()
    docs = []
    for i in doc_list.entry:
        docs.append(i.title.text)
    doc_num = None
    for i, j in enumerate(docs):
        if j == DOCUMENT_NAME:
            doc_num = i
    if doc_num == None:
        return 0
        
    entry = doc_list.entry[doc_num]
    content = client.download_resource_to_memory(entry)
    rows = ROW_RE.findall(content)
    if rows:
        for row in rows:
            row = row.split(',')
    return rows

def fix_name(name):
    fixed_name = ''
    for word in name.strip().split():
        if len(word) > 2:
            word = word.capitalize()
        fixed_name += ' ' + word
    return fixed_name.strip()

# Format raw database output for consumption by index template
# 0. SITE_ID
# 1. STORAGE_ID
# 2. STORAGE_TYPE_ID
# 3. GROSS_VOLUME
# 4. ULLAGE
# 5. GROSS_WATER_VOLUME
# 6. LAST_UPDATED
# 7. NAME (tank)
# 8. PRODUCT_NAME
# 9. NAME (store)
def format_stores(rows):
    sorted_rows = natsorted(rows, key=lambda x: x[-1])
    print 'ha'
    stores = []
    for name, tanks in groupby(sorted_rows, lambda x: x[9]):
        store = {}
        store['store_name'] = name
        
        tank_info = []
        for tank in tanks:
            new_tank = {}
            new_tank['tank_name'] = fix_name(tank[7])
            new_tank['product_name'] = fix_name(tank[8])
            new_tank['water_vol'] = float(tank[5])
            max = float(tank[3]) + float(tank[4]) + float(tank[5])
            new_tank['max_capacity'] = max
            new_tank['capacity'] = (float(tank[3]) + float(tank[5])) / max
            new_tank['last_updated'] = tank[6]
            tank_info.append(new_tank)
            
        # Find the row with the earliest time to use at the last update
        earliest = min(tank_info, key=lambda x: x['last_updated'])
        store['last_updated'] = earliest['last_updated'].strftime('%I:%M %p')

        store['tanks'] = tank_info
        stores.append(store)
    return stores

@route('/')
@view('index')
def index():
    rows = retrieve_doc()
    print 'ho'
    #stores = format_stores(rows)
    return { 'url': url, 'stores': rows }

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

debug(True)     # For development use only
# Reloader for development use only
run(host='10.0.0.27', port=8080, reloader=True)