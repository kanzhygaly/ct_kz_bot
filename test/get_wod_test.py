import datetime
import re

from bsoup_spider import BSoupParser

today = datetime.datetime.now().date()

url = 'https://comptrain.co/individuals/programming'
parser = BSoupParser(url=url)

# Remove anything other than digits
num = re.sub(r'\D', "", parser.get_wod_date())
wod_date = datetime.datetime.strptime(num, '%m%d%Y')

if wod_date.date().__eq__(today):
    title = parser.get_wod_date()
    reg_part = parser.get_regional_wod()
    open_part = parser.get_open_wod()
    description = reg_part + "\n" + open_part

    reg_text = (''.join(reg_part.split())).lower()
    reg_text = reg_text[4:25]
    open_text = (''.join(open_part.split())).lower()
    open_text = open_text[4:25]

    if not reg_text.startswith("qualifierathletesrest") and not open_text.startswith("openathletesrest"):
        print(title + "\n\n" + description)
        pass
    else:
        print(reg_text + "\n\n" + open_text)
else:
    print("Комплекс еще не вышел.\nСорян :(")


def test_old():
    weekday = {
        '0': 'sunday',
        '1': 'monday',
        '2': 'tuesday',
        '3': 'wednesday',
        '4': 'thursday',
        '5': 'friday',
        '6': 'saturday'
    }
    today = datetime.date(2018, 7, 9)
    index = today.strftime("%w")
    # target = today.strftime("%m-%d-%y")
    target = f'{today.month}-{today.day}-{str(today.year)[-2:]}'
    url = f'http://comptrain.co/individuals/workout/{weekday.get(index)}-·-{target}'
    try:
        parser = BSoupParser(url=url)
        title = parser.get_wod_date()

        description = parser.get_video_header()

        reg_part = parser.get_regional_wod()
        open_part = parser.get_open_wod()
        description = (description + "\n\n" + reg_part + open_part) if description else (reg_part + open_part)

        reg_text = (''.join(reg_part.split())).lower()
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
