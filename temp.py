# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pyodbc
from datetime import datetime, timedelta

server = getenv('SSA_SERVER')
db = getenv('SSA_DATABASE')
uid = getenv('SSA_UID')
pwd = getenv('SSA_PWD')

connection_string = 'DRIVER={{SQL Server}};SERVER={0};DATABASE={1};UID={2};'\
                    'PWD={3}'.format(server, db, uid, pwd)
                    
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()


def get_fields(cursor, table):
    col_name_query = """SELECT NAME 
        FROM syscolumns 
        WHERE id = object_id(?)"""
    cursor.execute(col_name_query, table)
    results = cursor.fetchall()
    ans = []
    for i in results:
        ans.append(i[0])
    return ans

date_query = """SELECT LAST_UPDATED
FROM dbo.LOG_INVENTORY 
WHERE LAST_UPDATED >= '2014-12-04'
AND 
LAST_UPDATED < '2014-12-05'"""

def get_tables(cursor):
    cursor.execute('SELECT * FROM sys.tables')
    results = cursor.fetchall()
    ans = []
    for i in results:
        ans.append(i[0])
    return ans

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

latest_query = """SELECT LAST_UPDATED
FROM dbo.LOG_INVENTORY
WHERE LAST_UPDATED >= ? AND LAST_UPDATED <= ?""" 

curr_time = datetime.now()
prev_time = curr_time - timedelta(minutes=15)
next_time = curr_time + timedelta(minutes=15)

curr_interval = get_time_int(curr_time)
prev_interval = get_time_int(prev_time)
next_interval = get_time_int(next_time)

#prev_query = latest_query + prev_interval[0] + ' AND LAST_UPDATED <= ' + prev_interval[1]
#next_query = latest_query + next_interval[0] + ' AND LAST_UPDATED <= ' + next_interval[1]
#latest_query += curr_interval[0] + ' AND LAST_UPDATED <= ' + curr_interval[1]
#print latest_query
#print prev_query
#print next_query
#test_query = """SELECT SITE_ID, STORAGE_ID, STORAGE_TYPE_ID, PRODUCT_LEVEL, GROSS_VOLUME, ULLAGE, WATER_LEVEL, GROSS_WATER_VOLUME, TEMPERATURE, NET_VOLUME
#    FROM LOG_INVENTORY
##    WHERE LAST_UPDATED >= ? AND LAST_UPDATED <= ? AND SITE_ID = 1"""

 
#test_query = """SELECT X.*, SITE.NAME FROM (SELECT inv.SITE_ID, inv.STORAGE_TYPE_ID, sto.NAME, 
#    sto.PRODUCT_NAME, sto.COMBINED_NAME, inv.GROSS_VOLUME, inv.ULLAGE, 
#    inv.GROSS_WATER_VOLUME
#    FROM LOG_INVENTORY inv
#    RIGHT JOIN STORAGE sto
#    ON inv.STORAGE_ID = sto.STORAGE_ID and 
#    inv.STORAGE_TYPE_ID = sto.STORAGE_TYPE_ID and 
#    inv.SITE_ID = sto.SITE_ID
#    WHERE inv.LAST_UPDATED BETWEEN ? AND ? and inv.STORAGE_TYPE_ID <> 102) X
#    RIGHT JOIN SITE
#    ON X.SITE_ID = SITE.SITE_ID
#    """

#test_query = """SELECT max(LAST_UPDATED), SITE_ID, STORAGE_ID, STORAGE_TYPE_ID,
#    GROSS_VOLUME, ULLAGE, GROSS_WATER_VOLUME
#    FROM LOG_INVENTORY
#    WHERE STORAGE_TYPE_ID <> 102
#    GROUP BY SITE_ID, STORAGE_ID, STORAGE_TYPE_ID, GROSS_VOLUME, ULLAGE,
#    GROSS_WATER_VOLUME
#    ORDER BY SITE_ID
#    """

#test_query = """SELECT *
#    FROM LOG_INVENTORY I1
#    WHERE LAST_UPDATED=(SELECT MAX(I2.LAST_UPDATED)
#                        FROM LOG_INVENTORY I2
#                        WHERE I1.SITE_ID = I2.SITE_ID AND
#                        I1.STORAGE_ID = I2.STORAGE_ID AND
#                        I1.STORAGE_TYPE_ID = I2.STORAGE_TYPE_ID AND
#                        I1.STORAGE_TYPE_ID <> 102)
#    ORDER BY SITE_ID
#    """

test_query = """SELECT tank_names.*, SITE.NAME FROM 
        (SELECT last.*, sto.NAME, sto.PRODUCT_NAME
        FROM (SELECT I1.SITE_ID, I1.STORAGE_ID, I1.STORAGE_TYPE_ID, I1.GROSS_VOLUME, I1.ULLAGE, I1.GROSS_WATER_VOLUME, I1.LAST_UPDATED
            FROM LOG_INVENTORY I1
            JOIN (
                SELECT MAX(LAST_UPDATED) AS LAST_UPDATED, SITE_ID, STORAGE_ID, STORAGE_TYPE_ID
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

#test_query = """SELECT STORAGE_ID, STORAGE_TYPE_ID, NAME, PRODUCT_NAME FROM STORAGE WHERE SITE_ID = 1"""

#cursor.execute(test_query, curr_interval)
cursor.execute(test_query)

rows = cursor.fetchall()

if rows:
    for row in rows:
        print row
else:
    cursor.execute(test_query, prev_interval)
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print row
    else:
        print "No current or previous interval data found"