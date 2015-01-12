# -*- coding: utf-8 -*-
"""
Created on Wed Jan 07 13:34:33 2015

@author: Administrator
"""

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

info = []


def fix_name(name):
    fixed_name = ''
    for word in name.strip().split():
        if len(word) > 2:
            word = word.capitalize()
        fixed_name += ' ' + word
    return fixed_name.strip()

with open('transitory.txt', 'rt') as f:
    for line in f:
        row = line.strip().split('|')
        info.append(row)

new_warning_levels = []

for row in info:
    new_row = []
    new_row.extend([row[-1], row[0], row[1], row[2], fix_name(row[-3]), fix_name(row[-2])])
    new_warning_levels.append(new_row)

for row in new_warning_levels:
    if row[5] not in WARNING_LEVELS[row[0]]:
        val = '0'
    else:
        val = str(WARNING_LEVELS[row[0]][row[5]])
    row = row.append(val)
        
#print new_warning_levels

with open('warning_levels.txt', 'wt') as f:
    for row in new_warning_levels:
        f.write('|'.join(row) + '\n')