from datetime import datetime
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
    regional = parser.get_regional_wod()
    openw = parser.get_open_wod()
    description = regional + "\n" + parser.get_open_wod()

    wod_id = None
    content = ''.join(regional.split()).lower()
    print(content)

    content = ''.join(openw.split()).lower()
    print(content)

    if content.startswith("2018regionalsathletesrest") and content.startswith("2018openathletesrest"):
        print(title + "\n\n" + description + "\n\n" + msg + "\n\n" + wod_id)
else:
    print("Комплекс еще не вышел.\nСорян :(")
