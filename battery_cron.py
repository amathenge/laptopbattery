#!/usr/bin/env python3
import sqlite3
from sms import sendSMS
import cred
import sys
from datetime import datetime

# A cron job to send the status of the battery at a specified interval.
# during testing - every 15 minutes
# but normally, once an hour (0.75 cents per SMS)

db = sqlite3.connect(cred.db_path+cred.db_name)
db.row_factory = sqlite3.Row
cur = db.cursor()

# id integer primary key AUTOINCREMENT,
# curdate CURRENT_TIMESTAMP,
# state varchar(16),
# energy varchar(16),
# energy_full varchar(16),
# energy_full_design varchar(16),
# energy_rate varchar(16),
# voltage varchar(16),
# time_remaining varchar(8),
# percentage_remaining varchar(8),
# design_capacity varchar(8)

# get the last 6 readings - this gives us 2 hours since cron is updating
# the database every 20 minutes.
# curdate = 2022-11-12 15:40:01
# state = [charging, discharging, fully-charged]
# energy = 40.000 Wh
# time_remaining = 6.1 hours or 23.4 minutes or 100%
# percentage_remaining = 67%
sql = '''
    select id, curdate, state, energy, time_remaining, percentage_remaining
    from battery
    order by id desc
    limit 6
'''
# need to calculate battery depletion for the last 2 readings
cur.execute(sql)
data = cur.fetchall()
db.close()

if data is None:
    sys.exit(-1)

rows = []
for row in data:
    rows.append({
        'id': row['id'],
        'curdate': row['curdate'],
        'state': row['state'],
        'time_remaining': row['time_remaining'],
        'percentage_remaining': row['percentage_remaining']
    })

num_rows = len(rows)

# need to calculate the difference between dates in two rows
def getTimeDiff(row1, row2):
    date1 = datetime.strptime(row1['curdate'], '%Y-%m-%d %H:%M:%S') 
    date2 = datetime.strptime(row2['curdate'], '%Y-%m-%d %H:%M:%S')
    return date1-date2

# get the remaining time in the battery from a row. We will use minutes.
# the battery reports time remaining in either:
# hours
# minutes
# %
# if reported in minutes - keep
# if reported in hours, convert to minutes by multiplying by 60
# if reported in percent (%), convert to minutes (assume 9 hours). Note that
# when the time is reported as a percent, it is always 100% (othewise it's reported)
# as hours or minutes.
def getTimeRemaining(row):
    time_str = row['time_remaining']
    time_type = ''
    if 'hours' in time_str:
        time_type = 'hours'
    elif 'minutes' in time_str:
        time_type = 'minutes'
    elif '%' in time_str:
        time_type = 'percent'
    time_str = time_str.replace('hours','')
    time_str = time_str.replace('minutes','')
    time_str = time_str.replace('%','')
    time_float = float(time_str)
    if time_type == 'hours':
        time_float *= 60
    elif time_type == 'percent':
        time_float = 9 * 60

    # round to remove the decimal place
    return round(time_float)

# get the remaining battery percentage from a row
def getPercentRemaining(row):
    percent_str = row['percentage_remaining']
    percent_str = percent_str.replace('%','')
    return float(percent_str)

# get the battery time loss between two rows in the table.
# row1 is the most recent row, row2 is the older row. Therefore if the
# battery is losing power, row1 will have less time (lower value) than row2
def getBatteryLoss_Time(row1, row2):
    remaining_time1 = getTimeRemaining(row1)
    remaining_time2 = getTimeRemaining(row2)
    return remaining_time1 - remaining_time2

# get the percentage battery loss between two rows in the table
# as with getBatteryLoss_Time() row1 is the most recent row, row2 is the older
# row. So if the battery is losing power, row1 will have a lower battery
# percentage left.
def getBatteryLoss_Percent(row1, row2):
    remaining_percent1 = getPercentRemaining(row1)
    remaining_percent2 = getPercentRemaining(row2)
    return remaining_percent1 - remaining_percent2

# create a list of the data to send via SMS. 
# this is a list of dicts.
sms_data = []
for row in range(num_rows-1):
    sms_data.append({
        'curdate': rows[row]['curdate'],
        'state': rows[row]['state'],
        'time_remaining': rows[row]['time_remaining'],
        'percentage_remaining': rows[row]['percentage_remaining'],
        'lost_time': getBatteryLoss_Time(rows[row], rows[row+1]),
        'lost_percent': getBatteryLoss_Percent(rows[row], rows[row+1])
    })

# function to create the text message. Take care not to use any characters that will
# be discarded by SMS (such as quotes)
def createMessage():
    message_items = 2
    msg = ''
    newline = '\n'
    for row in sms_data:
        if message_items > 0:
            msg += 'curdate: ' + row['curdate']
            msg += newline + 'state: ' + row['state']
            msg += newline + 'time_remaining: ' + row['time_remaining']
            msg += newline + 'percentage_remaining: ' + row['percentage_remaining']
            msg += newline + 'lost_time: ' + str(row['lost_time'])
            msg += newline + 'lost_percent: ' + str(row['lost_percent'])
            msg += newline + '------' + newline
            message_items -= 1
    return msg

message = createMessage()
# print(message)
# print(f'Message length: {len(message)}')

# now that we have the message, send it to tony
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
recipients = cred.recipients
result = sendSMS(message, recipients)
# print(str(result))
db = sqlite3.connect(cred.db_path+cred.db_name)
db.row_factory = sqlite3.Row
cur = db.cursor()
sql = '''
    insert into sms (curdate, result) values (?, ?)
'''
cur.execute(sql, [now, str(result)])
db.commit()
db.close()