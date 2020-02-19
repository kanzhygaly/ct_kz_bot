import datetime
from bsoup_spider import BSoupParser

today = datetime.datetime.now().date()

url = 'https://comptrain.co/wod'
parser = BSoupParser(url=url)

print(parser.get_wod_date())

open_part = parser.get_open_wod()
print(open_part)

reg_part = parser.get_regional_wod()
print(reg_part)

if reg_part.find("Rest Day") != -1 and open_part.find("Rest Day") != -1:
    print('Rest Day 1')
else:
    print('WOD 1')

if reg_part.find("Rest Day") == -1 or open_part.find("Rest Day") == -1:
    print('WOD 2')
else:
    print("Rest Day 2")
