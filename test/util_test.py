import datetime

from constants.date_format import D_M_Y, A_D_B, D_B, H_M_S_D_B_Y, M_D_Y, sD_B_Y, WEEKDAY
from util.db_util import database_url_parse

now = datetime.datetime.now()

# test substring
msg = 'CHOOSE_DAY_120318'
print(msg[0:10])
print(msg[11:])

# test timedelta
wod_day = datetime.datetime.strptime('060618', D_M_Y).date()
timedelta = now.date() - wod_day
print(timedelta.days)

print('date_format')
print(wod_day.strftime(D_M_Y))
print(now.strftime(H_M_S_D_B_Y))
print(now.strftime(M_D_Y))
print(now.strftime(sD_B_Y))
print(now.strftime(WEEKDAY))


def test_find_wod():
    print('test_find_wod')

    row = []
    count = 5
    while count > 0:
        if len(row) < 3:
            d = now - datetime.timedelta(days=count)
            # 07 April
            row.append(d.strftime(D_B))
            count -= 1
        else:
            print(row)
            row = []

    row.append("Today")
    print(row)


def test_add_wod() -> list:
    keyboard = []
    row = []
    count = 9
    date = now

    # if today is Thursday then include it
    if date.weekday() == 3:
        count = 8
        row.append(date.strftime(A_D_B))

    while count >= 0:
        if len(row) < 3:
            if date.weekday() <= 3:
                delta = 1 + date.weekday()
                date = date - datetime.timedelta(days=delta)
            elif date.weekday() > 3:
                delta = date.weekday() - 3
                date = date - datetime.timedelta(days=delta)

            # Thu 18 Apr
            btn_name = date.strftime(A_D_B)
            row.append(btn_name)
            count -= 1
        else:
            keyboard.append(row)
            row = []

    return keyboard


test_find_wod()

print('test_add_wod')
print(test_add_wod())

print('database_url_parse')
credentials = database_url_parse('postgres://username:userpassword@hostname:5432/dbname')
print(credentials)

print('list tests')
result = [1, 2, 3, 4, 5]
print(result[-1])
