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

EXPIRED_TIME = 17   # Number of minutes after which a time is expired

# From levels Marc sent
WARNING_LEVELS = {
    'Shortstop 1' : {
        'Unlead A, Unlead B' : 4128,
        'Prem.' : 500,
        'Diesel' : 716
    },
    'Shortstop 3' : {
        'Unlead' : 1453,
        'Premium' : 536,
        'Diesel' : 500
    },
    'Shortstop 4' : {
        'Unlead' : 3765,
        'Premium' : 771,
        'Diesel' : 3120
    },
    'Shortstop 8' : {
        'Unleaded' : 4815,
        'Premium' : 1012,
        'Diesel' : 2117,
        'Unlead WE' : 1404,
        'Unlead WW' : 3500,
        'Diesel West' : 742
    },
    'Shortstop 10' : {
        'Unleaded' : 4028,
        'Premium' : 790,
        'Diesel' : 874
    },
    'Shortstop 12' : {
        'Unleaded' : 4510,
        'Premium' : 622,
        'Diesel' : 657
    },
    'Shortstop 13' : {
        'Unleaded' : 9506,
        'Diesel' : 6622,
        'Premium' : 1133,
        'Def' : 1500
    },
    'Shortstop 16' : {
        'Unleaded' : 4998,
        'Premium' : 794,
        'Diesel' : 707
    },
    'Shortstop 18' : {
        'Unleaded' : 2782,
        'Premium' : 633,
        'Diesel' : 850
    },
    'Shortstop 20' : {
        'Unleaded' : 6991,
        'Premium' : 687,
        'Diesel' : 890,
        'Diesel LG' : 1235
    },
    'Shortstop 21' : {
        'Unleaded' : 2429,
        'Diesel' : 848
    },
    'Shortstop 22' : {
        'Unleaded' : 2360,
        'Premium' : 500,
        'Diesel, Diesel' : 3766
    },
    'Shortstop 23' : {
        'Unlead 1, Unlead 2' : 6972,
        'Premium' : 803,
        'Diesel' : 610
    },
    'Shortstop 24' : {
        'Unleaded A, Unleaded B' : 4356,
        'Premium' : 791,
        'Diesel A, Diesel B' : 4142
    },
    'Shortstop 25' : {
        'Unlead' : 2733,
        'Premium' : 528,
        'Diesel' : 3422
    },
    'Shortstop 26' : {
        'Unleaded' : 2107,
        'Premium' : 614,
        'E-15' : 589,
        'Diesel' : 768
    }
}

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
        I1.GROSS_VOLUME, I1.ULLAGE, I1.GROSS_WATER_VOLUME, I1.WATER_LEVEL, 
        I1.LAST_UPDATED
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
# 6. WATER_LEVEL
# 7. LAST_UPDATED
# 8. NAME (tank)
# 9. PRODUCT_NAME
# 10. NAME (store)
# TODO: fix - 11 - 14 added by add_levels(), currently not available
# 11. high level
# 12. low level
# 13. delivery needed level
# 14. water level limit
def format_stores(rows):
    stores = []
    for name, tanks in groupby(rows, lambda x: x[10]):
        store = {}
        store['store_name'] = name
        
        tank_info = []
        for tank in tanks:
            new_tank = {}
            new_tank['tank_name'] = fix_name(tank[8])
            new_tank['product_name'] = fix_name(tank[9])
#            new_tank['water_level'] = tank[6]
            new_tank['gross_volume'] = int(tank[3]) if tank[3] is not None else None
            new_tank['ullage'] = int(tank[4]) if tank[4] is not None else None
#            max = tank[3] + tank[4] + tank[5]
#            new_tank['max_capacity'] = max
#            new_tank['capacity'] = float(tank[3] + tank[5])
            new_tank['last_updated'] = tank[7]
            new_tank['tank_low'] = False
            # For the most part the manifolds have a different product name
            # than the other tanks.  Shortstop 25 tanks 1, 2, and the manifold
            # all have product name 'Unlead'
            if name != 'Shortstop 25':
                warn_lvl = WARNING_LEVELS[name].get(new_tank['product_name'], 0)
            elif '1' not in new_tank['tank_name'] and \
                 '2' not in new_tank['tank_name']:
                warn_lvl = WARNING_LEVELS[name].get(new_tank['product_name'], 0)
            else:
                warn_lvl = 0
            if new_tank['gross_volume'] <= warn_lvl:
                new_tank['tank_low'] = True
#            # If no delivery needed number, use low level
#            deliv_needed = tank[12] if tank[13] < 0.5 else tank[13]
#            # Calculate params needed for meters
#            new_tank['low'] = deliv_needed * 1.25  # Turn red at 25% buffer
#            new_tank['high'] = deliv_needed * 1.50 # Turn yellow at 50% buffer
#            new_tank['optimum'] = new_tank['high'] + 1  # Green above high
#            new_tank['water_level_limit'] = tank[14]
            tank_info.append(new_tank)
            
        # Find the row with the earliest time to use at the last update
        earliest = min(tank_info, key=lambda x: x['last_updated'])
        store['last_update_time'] = earliest['last_updated'].strftime('%I:%M %p')
        store['last_update_date'] = earliest['last_updated'].strftime("%b %d, '%y")
        
        # If old date/time, set expired flags
        if earliest['last_updated'].date() != datetime.today().date():
            store['date_expired'] = True
        else:
            store['date_expired'] = False
        if (earliest['last_updated'] + timedelta(minutes=EXPIRED_TIME)) < datetime.now():
            store['time_expired'] = True
        else:
            store['time_expired'] = False
            
        store['tanks'] = tank_info
        stores.append(store)
    return stores

# tank_data.csv doesn't contain manifold info, so this function messes with
# data from get_latest_updates()
# TODO: fix so it plays nicely with manifolds (STORAGE_TYPE_ID = 101)
def add_levels(rows):
    temp_rows = []
    new_rows = []
    for row in rows:
        temp_rows.append(tuple(row))
    with open('tank_data.csv', 'rt') as f:
        for i, line in enumerate(f):
            print line
            items = line.strip().split(',')
            try:
                high = float(items[-5])
            except:
                high = 0.0
            try:
                low = float(items[-4])
            except:
                low = 0.0
            try:
                deliv_needed = float(items[-2])
            except:
                deliv_needed = 0.0
            try:
                water_level_limit = float(items[-1])
            except:
                water_level_limit = 3.0
            new_row = temp_rows[i] + tuple([high, low, deliv_needed, 
                                            water_level_limit])
            new_rows.append(new_row)
    return new_rows

@route('/')
@view('index')
def index():
    rows = get_latest_updates()
    rows = natsorted(rows, key=lambda x: x[-1])
#    rows = add_levels(rows)
    stores = format_stores(rows)
    return { 'url': url, 'stores': stores }

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

debug(True)     # For development use only
# Reloader for development use only
run(host='10.0.0.27', port=8080, reloader=True)

#rows = get_latest_updates()
#rows = natsorted(rows, key=lambda x: x[-1])
#print rows
#rows = add_levels(rows)
#print rows
#stores = format_stores(rows)
