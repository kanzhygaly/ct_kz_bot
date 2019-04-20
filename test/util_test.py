import datetime

now = datetime.datetime.now()

# test substring
msg = 'CHOOSE_DAY_120318'
print(msg[0:10])
print(msg[11:])

# test timedelta
wod_day = datetime.datetime.strptime('060618', '%d%m%y').date()
timedelta = now.date() - wod_day
print(timedelta.days)


def test_find_wod():
    row = []
    count = 5
    while count > 0:
        if len(row) < 3:
            d = now - datetime.timedelta(days=count)
            # 07 April
            row.append(d.strftime("%d %B"))
            count -= 1
        else:
            print(row)
            row = []

    row.append("Today")
    print(row)


def test_add_wod():
    keyboard = []
    row = []
    count = 9
    date = now

    while count >= 0:
        if len(row) < 3:
            if date.weekday() <= 3:
                delta = 1 + date.weekday()
                date = date - datetime.timedelta(days=delta)
            elif date.weekday() > 3:
                delta = date.weekday() - 3
                date = date - datetime.timedelta(days=delta)

            # Thu 18 Apr
            btn_name = date.strftime("%a %d %b")
            row.append(btn_name)
            count -= 1
        else:
            keyboard.append(row)
            row = []

    print(keyboard)


test_add_wod()
