# -*- coding: utf-8 -*-
"""
Created on Wed Dec 24 08:14:10 2014

@author: Administrator
"""

# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pyodbc
from os import getenv
import pandas as pd
from natsort import natsorted

server = getenv('SSA_SERVER')
db = getenv('SSA_DATABASE')
uid = getenv('SSA_UID')
pwd = getenv('SSA_PWD')

connection_string = 'DRIVER={{SQL Server}};SERVER={0};DATABASE={1};UID={2};'\
                    'PWD={3}'.format(server, db, uid, pwd)
                    
conn = pyodbc.connect(connection_string)
cursor = conn.cursor()

test_query = """
    SELECT x.*, SITE.NAME FROM
        (SELECT SITE_ID, STORAGE_TYPE_ID, STORAGE_ID, NAME, PRODUCT_NAME 
        FROM STORAGE WHERE STORAGE_TYPE_ID = 100) x
        RIGHT JOIN SITE
        ON x.SITE_ID = SITE.SITE_ID
    """

cursor.execute(test_query)

rows = cursor.fetchall()
rows = natsorted(rows, key= lambda x: x[-1])  # Want them sorted by store name

index = ['site', 'stor_type', 'tank_num', 'tank_name', 'product_name', 'store_name']
tanks = pd.DataFrame.from_records(rows, columns=index)

with open('tnksetup.tsv', 'rt') as f:
    data = []
    for line in f:
        row = line.strip().replace('"', '').replace(',', '').split('\t')
        data.append(tuple(row[25:-4]))
del data[36]    # Appears to be a manifold that doesn't show up elsewhere
data = data[4:] + data[:4]   # Store 26 comes first, want it last

col_names = ['capacity', 'diameter', 'max_product', 'high', 'low', 'overfill', 'delivery_limit']
tank_data = pd.DataFrame.from_records(data, columns=col_names)

final = pd.concat([tanks, tank_data], axis=1)
with open('tank_data.csv', 'wt') as f:
    f.write(final.to_csv(header=False, index=False))

cursor.close()
del cursor
conn.close()