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


def get_latest_updates():
    # Get numbers from LOG_INVENTORY, JOIN with STORAGE to get tank and product
    # names, then JOIN with SITE to get store names, excluding 
    # STORAGE_TYPE_ID 102, which doesn't show up in SSA website
    test_query = """SELECT tank_names.*, SITE.NAME FROM 
        (SELECT last.*, sto.NAME, sto.PRODUCT_NAME
        FROM (SELECT I1.SITE_ID, I1.STORAGE_ID, I1.STORAGE_TYPE_ID, 
        I1.GROSS_VOLUME, I1.ULLAGE, I1.GROSS_WATER_VOLUME, I1.LAST_UPDATED
            FROM LOG_INVENTORY I1
            JOIN (
                SELECT MAX(LAST_UPDATED) AS LAST_UPDATED, SITE_ID, 
                STORAGE_ID, STORAGE_TYPE_ID
                FROM LOG_INVENTORY
                GROUP BY SITE_ID, STORAGE_ID, STORAGE_TYPE_ID) as I2
                ON I1.SITE_ID = I2.SITE_ID AND
                I1.STORAGE_ID = I2.STORAGE_ID AND
                I1.STORAGE_TYPE_ID = I2.STORAGE_TYPE_ID AND
                I1.LAST_UPDATED = I2.LAST_UPDATED
            WHERE I1.STORAGE_TYPE_ID <> 102) last
        RIGHT JOIN STORAGE sto
        ON last.STORAGE_ID = sto.STORAGE_ID AND
        last.STORAGE_TYPE_ID = sto.STORAGE_TYPE_ID AND
        last.SITE_ID = sto.SITE_ID) tank_names
        RIGHT JOIN SITE
        ON tank_names.SITE_ID = SITE.SITE_ID
    ORDER BY tank_names.SITE_ID
    """
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()
    cursor.execute(test_query)
    rows = cursor.fetchall()
    cursor.close()
    del cursor
    conn.close()
    
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
    stores = []
    for name, tanks in groupby(sorted_rows, lambda x: x[9]):
        store = {}
        store['store_name'] = name
        
        tank_info = []
        for tank in tanks:
            new_tank = {}
            new_tank['tank_name'] = fix_name(tank[7])
            new_tank['product_name'] = fix_name(tank[8])
            new_tank['water_vol'] = tank[5]
            max = tank[3] + tank[4] + tank[5]
            new_tank['max_capacity'] = max
            new_tank['capacity'] = float(tank[3] + tank[5]) / max
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
    # colors: blue #00f, yellow #ff0, green #0f0
#    test_str = '<b>Hello {{name}}</b>! \n {{names}}\n'\
#                '<svg height=50><g>'\
#                '<rect y="0" x="0" width="150" height="20" fill="#000"></rect>'\
#                '<rect y="1" x="1" width="148" height="18" fill="#fff"></rect>'\
#                '<rect y="1" x="1" width="5" height="18" fill="#00f"></rect>'\
#                '<rect y="1" x="6" width="100" height="18" fill="#0f0"></rect>'\
#                '</g></svg>'
    #return template(test_str, name=name, names=column_names)
    rows = get_latest_updates()
    stores = format_stores(rows)
    #store_boxes = format_stores(rows)
    return { 'url': url, 'stores': stores } #template('test_template', rows=rows)

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

debug(True)     # For development use only
# Reloader for development use only
run(host='10.0.0.27', port=8080, reloader=True)