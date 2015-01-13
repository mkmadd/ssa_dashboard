# -*- coding: utf-8 -*-
"""
Created on Thu Dec 04 14:27:01 2014

@author: Michael K. Maddeford
"""

from bottle import route, run, debug, static_file, url, view
from os import getenv
from datetime import datetime, timedelta
from natsort import natsorted
from itertools import groupby
import gdata.docs.client
import re

ROW_RE = re.compile('<span>(.*?)</span>')  #To extract data from google doc
TEMP_FILE = 'transitory.txt'
DOCUMENT_NAME = 'SSA Doc' # google docs name
username = getenv('GOOG_UID') # google/gmail login id
passwd = getenv('GOOG_PWD') # google/gmail login password


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
            new_tank['site_id'] = tank[0]
            new_tank['storage_id'] = tank[1]
            new_tank['tank_name'] = fix_name(tank[8])
            new_tank['product_name'] = fix_name(tank[9])
            new_tank['gross_volume'] = int(tank[3]) if tank[3] is not None else None
            new_tank['ullage'] = int(tank[4]) if tank[4] is not None else None
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
        sep_rows = []
        for row in rows:
            temp = row.split('|')
            sep_rows.append(temp)
    return sep_rows


#@route('/alarms')
#@view('alarm')
#def show_alarms():
#    alarms = get_todays_active_alarms()
#    alarms = natsorted(alarms, key=lambda x: x[0])
#    #alarms = format_alarms(alarms)
#    return { 'url': url, 'alarms': alarms}
    

@route('/')
@view('index')
def index():
    rows = retrieve_doc()
    rows = natsorted(rows, key=lambda x: x[-1])
    stores = format_stores(rows)
    return { 'url': url, 'stores': stores, 'alarms': [None] }

@route('/static/:path#.+#', name='static')
def static(path):
    return static_file(path, root='static')

debug(True)     # For development use only
# Reloader for development use only
#run(host='10.0.0.27', port=8080, reloader=True)
rows = retrieve_doc()
print rows[:5]