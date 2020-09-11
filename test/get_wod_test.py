import datetime

from bsoup_spider import BSoupParser
from util.parser_util import parse_wod_date

today = datetime.datetime.now().date()

url = 'https://comptrain.co/wod'
parser = BSoupParser(url=url)

wod_string = parser.get_wod_date()
print(wod_string)

print(parse_wod_date(wod_string))

open_part = parser.get_open_wod()
print(open_part)

reg_part = parser.get_regional_wod()
print(reg_part)

if reg_part.lower().find("rest day") != -1 and open_part.lower().find("rest day") != -1:
    print('Rest Day 1')
else:
    print('WOD 1')

if reg_part.lower().find("rest day") == -1 or open_part.lower().find("rest day") == -1:
    print('WOD 2')
else:
    print("Rest Day 2")
