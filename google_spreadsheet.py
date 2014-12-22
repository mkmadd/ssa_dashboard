# -*- coding: utf-8 -*-
"""
Created on Fri Dec 12 13:42:51 2014

@author: Michael K. Maddeford
"""

import pyodbc
from os import getenv
from natsort import natsorted
from itertools import groupby

server = getenv('SSA_SERVER')
db = getenv('SSA_DATABASE')
uid = getenv('SSA_UID')
pwd = getenv('SSA_PWD')

connection_string = 'DRIVER={{SQL Server}};SERVER={0};DATABASE={1};UID={2};'\
                    'PWD={3}'.format(server, db, uid, pwd)

cnxn = pyodbc.connect(connection_string)
cursor = cnxn.cursor()

def get_latest_updates(cursor):
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
    cursor.execute(test_query)
    return cursor.fetchall()

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

if __name__ == __main__:
    rows = get_latest_updates(cursor)
    stores = format_stores(rows)
