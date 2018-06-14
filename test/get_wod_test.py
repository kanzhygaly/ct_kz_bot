from datetime import datetime, timedelta
import re

from bsoup_spider import BSoupParser

msg = "/wod_results\n\n" \
      "/add_wod_result"

now = datetime.now()

url = 'http://comptrain.co/individuals/home'
parser = BSoupParser(url=url)

# Remove anything other than digits
num = re.sub(r'\D', "", parser.get_wod_date())
wod_date = datetime.strptime(num, '%m%d%y')
print(wod_date)

if wod_date.date().__eq__(now.date()):
    title = parser.get_wod_date()
    regional_part = parser.get_regional_wod()
    open_part = parser.get_open_wod()
    description = regional_part + "\n" + open_part

    reg_text = (''.join(regional_part.split())).lower()
    reg_text = reg_text[4:]
    open_text = (''.join(open_part.split())).lower()
    open_text = open_text[4:]

    if not reg_text.startswith("regionalsathletesrest") and not open_text.startswith("openathletesrest"):
        print(title + "\n\n" + description + "\n\n" + msg)
    else:
        print(reg_text + "\n\n" + open_text)
else:
    print("Комплекс еще не вышел.\nСорян :(")


