from datetime import datetime, timedelta
import re

from bsoup_spider import BSoupParser

now = datetime.now()

url = 'http://comptrain.co/individuals/home'
parser = BSoupParser(url=url)

# Remove anything other than digits
num = re.sub(r'\D', "", parser.get_wod_date())
wod_date = datetime.strptime(num, '%m%d%y')
print(wod_date)

today = now.date()

if wod_date.date().__eq__(today):
    title = parser.get_wod_date()
    regional_part = parser.get_regional_wod()
    open_part = parser.get_open_wod()
    description = regional_part + "\n" + open_part

    reg_text = (''.join(regional_part.split())).lower()
    reg_text = reg_text[4:]
    open_text = (''.join(open_part.split())).lower()
    open_text = open_text[4:]

    if not reg_text.startswith("regionalsathletesrest") and not open_text.startswith("openathletesrest"):
        print(title + "\n\n" + description)
        pass
    else:
        print(reg_text + "\n\n" + open_text)
else:
    print("Комплекс еще не вышел.\nСорян :(")

weekday = {
    '0': 'sunday',
    '1': 'monday',
    '2': 'tuesday',
    '3': 'wednesday',
    '4': 'thursday',
    '5': 'friday',
    '6': 'saturday'
}
index = today.strftime("%w")
target = today.strftime("%m-%d-%y").lstrip("0").replace("0", "")
url = f'http://comptrain.co/individuals/workout/{weekday.get(index)}-·-{target}'
try:
    parser = BSoupParser(url=url)
    regional_part = parser.get_regional_wod()
    open_part = parser.get_open_wod()
    description = regional_part + "\n" + open_part

    reg_text = (''.join(regional_part.split())).lower()
    reg_text = reg_text[4:]
    open_text = (''.join(open_part.split())).lower()
    open_text = open_text[4:]

    if not reg_text.startswith("regionalsathletesrest") and not open_text.startswith("openathletesrest"):
        print(title + "\n\n" + description)
    else:
        print(reg_text + "\n\n" + open_text)
except Exception as e:
    print(e)
    print("Комплекс еще не вышел.\nСорян :(")
