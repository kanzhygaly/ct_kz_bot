import datetime

now = datetime.datetime.now()
row = []
count = 5
while count > 0:
    if len(row) < 3:
        d = now - datetime.timedelta(days=count)
        row.append(d.strftime("%d %B"))
        count -= 1
    else:
        print(row)
        row = []

row.append("Today")
print(row)

msg = 'CHOOSE_DAY_120318'
print(msg[0:10])
print(msg[11:])

wod_day = datetime.datetime.strptime('060618', '%d%m%y').date()
timedelta = now.date() - wod_day
print(timedelta.days)
