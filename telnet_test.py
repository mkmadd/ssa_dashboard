# -*- coding: utf-8 -*-
"""
Created on Wed Dec 31 10:44:11 2014

@author: Administrator
"""

import telnetlib

HOST='10.1.1.50'
PORT=10001

tn = telnetlib.Telnet(HOST, PORT)

tn.write('\x01')
tn.write('I20100')
test = tn.read_eager()
print test
tn.write('exit\n')
print tn.read_all()
