#!/usr/bin/python
#
#
#  1) Install the google documents python api
#  2) Create a spreadsheet in google documents and save it under a name
#     that matches SPREADSHEET_NAME
#  3) Name the column headings of the google spreadsheet 'ip','date','time'
#  4) Edit USERNAME and PASSWD to match your login info
#  5) Make this file executable
#  6) In a terminal window, type 'crontab -e' and add this script to your
#  user's crontab. ex. 56 * * * * /usr/bin/python /path_to_your_script/googleIP.py
#

## Change These to Match Your Info!

import pyodbc
from os import getenv
from natsort import natsorted
from itertools import groupby
import gdata.docs.client

SPREADSHEET_NAME = 'SSA Data' # google documents spreadsheet name
DOCUMENT_NAME = 'SSA Doc' # google docs name
USERNAME = getenv('GOOG_UID') # google/gmail login id
PASSWD = getenv('GOOG_PWD') # google/gmail login password

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



## Function Definitions

def StringToDictionary(row_data):
  result = {}
  for param in row_data.split():
    name, value = param.split('=')
    result[name] = value
  return result

def load():
  gd_client = gdata.spreadsheet.service.SpreadsheetsService()
  gd_client.email = USERNAME
  gd_client.password = PASSWD
  gd_client.ProgrammaticLogin()
  return gd_client
  
def load_docs():
    client = gdata.docs.client.DocsClient(source='drive_test')
    client.ClientLogin(USERNAME, PASSWD, client.source)
    return client

def updateSheet(updates):
  gd_client = load()
  docs= gd_client.GetSpreadsheetsFeed()
  spreads = []
  for i in docs.entry: spreads.append(i.title.text)
  spread_number = None
  for i,j in enumerate(spreads):
    if j == SPREADSHEET_NAME: spread_number = i
  if spread_number == None:
    return 0

  key = docs.entry[spread_number].id.text.rsplit('/', 1)[1]
  feed = gd_client.GetWorksheetsFeed(key)
  wksht_id = feed.entry[0].id.text.rsplit('/', 1)[1]
  feed = gd_client.GetListFeed(key,wksht_id)
  num_rows = int(feed.total_results.text)
  if num_rows >= 1:
      for i in range(num_rows+1):
          gd_client.DeleteRow(feed.entry[0])
  for update in updates:
      entry = gd_client.InsertRow(update,key,wksht_id)
  return 1
  
def updateDoc():
    client = load_docs()
    doc_list = client.GetResources()
    docs = []
    for i in doc_list.entry:
        docs.append(i.title.text)
    doc_num = None
    for i, j in enumerate(docs):
        if j == DOCUMENT_NAME:
            doc_num = i
    if doc_num == None:
        return 0
        
    key = doc_list.entry[doc_num].id.text.rsplit('/', 1)[1]
    entry = doc_list.entry[doc_num]#client.GetResourceById('17UiGtHT4D3Mae9EljgXvKjGknvHL8U0DLtkxlYkhlWA')
    media = gdata.data.MediaSource()
    media.set_file_handle('transitory.txt', 'text/txt')
    client.update_resource(entry, media=media, update_metadata=False)
  
def write_file(rows):
    with open('transitory.txt', 'wt') as f:
        for row in rows:
            f.write(','.join(str(e) for e in row))
                
#        new_dict = {}
#        new_dict['last-update'] = str(row[6])
#        new_dict['store'] = row[9]
#        new_dict['tank'] = row[7]
#        new_dict['product'] = row[8]
#        new_dict['gross-volume'] = str(row[3])
#        new_dict['ullage'] = str(row[4])
#        new_dict['gross-water'] = str(row[5])
#        dicts.append(new_dict)
#    return dicts
        
            

if __name__ == '__main__':
    server = getenv('SSA_SERVER')
    db = getenv('SSA_DATABASE')
    uid = getenv('SSA_UID')
    pwd = getenv('SSA_PWD')
    
    connection_string = 'DRIVER={{SQL Server}};SERVER={0};DATABASE={1};UID={2};'\
                        'PWD={3}'.format(server, db, uid, pwd)
    
    cnxn = pyodbc.connect(connection_string)
    cursor = cnxn.cursor()
    
    rows = get_latest_updates(cursor)

#    status = updateSheet(make_dict_list(rows))
    write_file(rows)
    status = updateDoc()
    
    
    if status == 1:
        print 'Success'
    elif status == 0:
        print 'Crushing failure!'
    