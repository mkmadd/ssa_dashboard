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
import gdata.docs.client
import re

ROW_RE = re.compile('<span>(.*?)</span>')
TEMP_FILE = 'transitory.txt'
DOCUMENT_NAME = 'SSA Doc' # google docs name
username = getenv('GOOG_UID') # google/gmail login id
passwd = getenv('GOOG_PWD') # google/gmail login password

# Parameters for SQL Server connection
server = getenv('SSA_SERVER')
db = getenv('SSA_DATABASE')
uid = getenv('SSA_UID')
pwd = getenv('SSA_PWD')

connection_string = 'DRIVER={{SQL Server}};SERVER={0};DATABASE={1};UID={2};'\
                    'PWD={3}'.format(server, db, uid, pwd)


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

def load_docs():
    client = gdata.docs.client.DocsClient(source='drive_test')
    client.ClientLogin(username, passwd, client.source)
    return client

def update_doc():
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
    media = gdata.data.MediaSource()
    media.set_file_handle(TEMP_FILE, 'text/txt')
    client.update_resource(entry, media=media, update_metadata=False)
    
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
            row = row.split('|')
    return rows
    

# Write rows to temporary file
# TODO - exception handling
def write_file(rows):
    with open(TEMP_FILE, 'wt') as f:
        for row in rows:
            f.write('|'.join(str(e) for e in row) + '\n')  # Commas in data


if __name__ == '__main__':
    rows = get_latest_updates()   # Get data from SQL Server
    write_file(rows)   # Write data to temp file
    status = update_doc()  # Copy temp file to Google Docs
    #status = retrieve_doc()
    
    if status == 1:
        print 'Success'
    elif status == 0:
        print 'Crushing failure!'
