# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 09:43:56 2014

@author: administrator
"""

import pyodbc
from os import getenv

server = getenv('SSA_SERVER')
db = getenv('SSA_DATABASE')
uid = getenv('SSA_UID')
pwd = getenv('SSA_PWD')

connection_string = 'DRIVER={{SQL Server}};SERVER={0};DATABASE={1};UID={2};'\
                    'PWD={3}'.format(server, db, uid, pwd)

connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

def get_fields(cursor, table):
    # Get column names for given table
    col_name_query = """SELECT NAME 
        FROM syscolumns 
        WHERE id = object_id(?)"""
    cursor.execute(col_name_query, table)
    results = cursor.fetchall()
    ans = []
    for i in results:
        ans.append(i[0])
    return ans

def get_tables(cursor):
    # Get all tables in database
    table_query = "SELECT * FROM sys.tables"
    cursor.execute(table_query)
    results = cursor.fetchall()
    ans = []
    for i in results:
        ans.append(i[0])
    return ans

if __name__ == '__main__':
    tables = get_tables(cursor)
    with open('db_info.txt', 'wt') as f, open('db_info.csv', 'wt') as f1:
        for table in tables:
            fields = get_fields(cursor, table)
            f.write(table + '\n')
            f1.write(table + '\n')
            f.write('------------------------\n\n')
            f1.write('------------------------\n\n')
            for field in fields:
                f.write(field + '\n')
                f1.write(field + ', ')
            f.write('\n\n')
            f1.write('\n\n')
    