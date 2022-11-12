#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime
import cred

# get current date/time at the top of the script - there was an idea to use this data, but we
# are going to use the CURRENT_TIMESTAMP keyword to get that field populated.
now = datetime.now()
now_date = now.strftime('%Y-%m-%d')
now_time = now.strftime('%H:%M:%S')
now_timestring = now_date + ' ' + now_time

# interrogate the battery to get status information.
data = os.popen("upower -i `upower -e | grep 'BAT'`").read()

def getfield(item):
    item = item.split(':')
    data = item[1].strip()
    return data

# parse fields and log into a database
# mapping -> field = item
# 11 = battery state 
# 13 = energy (remaining)
# 15 = energy full
# 16 = energy design full (new)\
# 17 = energy rate
# 18 = voltage
# 19 = time (hours) left (to empty)
# 20 = percentage left (to empty)
# 21 = design capacity (percent)
data = data.split('\n')

battery = {
    'curdate': now_timestring,
    'state': getfield(data[11]),
    'energy': getfield(data[13]),
    'energy_full': getfield(data[15]),
    'energy_full_design': getfield(data[16]),
    'energy_rate': getfield(data[17]),
    'voltage': getfield(data[18]),
    'time_remaining': getfield(data[19]),
    'percentage_remaining': getfield(data[20]),
    'design_capacity': getfield(data[21])
}
# print(list(battery.values()))

def getSQL():
    return '''
        insert into battery (curdate, state, energy, energy_full, energy_full_design,
        energy_rate, voltage, time_remaining, percentage_remaining, design_capacity)
        values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

dbfilename = cred.db_path+cred.db_name
db = sqlite3.connect(dbfilename)
db.row_factory = sqlite3.Row
cur = db.cursor()
sql = getSQL()
cur.execute(sql, list(battery.values()))
db.commit()
db.close()