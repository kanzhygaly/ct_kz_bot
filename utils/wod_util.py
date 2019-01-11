import os
import re
import pytz
from datetime import datetime
from bsoup_spider import BSoupParser
from db import user_db, wod_db, wod_result_db, location_db


async def get_wod():
    today = datetime.now().date()

    result = await wod_db.get_wods(today)
    if result:
        wod_id = result[0].id
        title = result[0].title
        description = result[0].description

        return title + "\n\n" + description, wod_id

    parser = BSoupParser(url=os.environ['WEB_URL'])

    # Remove anything other than digits
    # num = re.sub(r'\D', "", parser.get_wod_date())
    num = ''.join(c for c in parser.get_wod_date() if c.isdigit() or c == '.')
    wod_date = datetime.strptime(num, '%m.%d.%Y')

    # if wod_date.date().__eq__(today):
    if wod_date.day.__eq__(today.day) and wod_date.month.__eq__(today.month) and wod_date.year.__eq__(today.year):
        title = parser.get_wod_date()

        reg_part = parser.get_regional_wod()
        open_part = parser.get_open_wod()
        description = reg_part + "\n" + open_part

        reg_text = (''.join(reg_part.split())).lower()
        reg_text = reg_text[4:25]
        open_text = (''.join(open_part.split())).lower()
        open_text = open_text[4:25]

        wod_id = None
        if not reg_text.startswith("qualifierathletesrest") and not open_text.startswith("openathletesrest"):
            wod_id = await wod_db.add_wod(today, title, description)

        return title + "\n\n" + description, wod_id
    else:
        return "Комплекс еще не вышел.\nСорян :(", None


async def get_wod_results(user_id, wod_id):
    location = await location_db.get_location(user_id)

    wod_results = await wod_result_db.get_wod_results(wod_id)

    if wod_results:
        msg = ''
        for res in wod_results:
            u = await user_db.get_user(res.user_id)

            dt = res.sys_date.astimezone(pytz.timezone(location.tz)) if location else res.sys_date
            name = f'{u.name} {u.surname}' if u.surname else u.name

            title = '_' + name + ', ' + dt.strftime("%H:%M:%S %d %B %Y") + '_'
            msg += f'{title}\n' \
                   f'{res.result}\n\n'

        return msg
    else:
        return None


async def reset_wod():
    today = datetime.now().date()

    result = await wod_db.get_wod_by_date(today)
    wod_id = result.id

    parser = BSoupParser(url=os.environ['WEB_URL'])

    # Remove anything other than digits
    # num = re.sub(r'\D', "", parser.get_wod_date())
    num = ''.join(c for c in parser.get_wod_date() if c.isdigit() or c == '.')
    wod_date = datetime.strptime(num, '%m.%d.%Y')

    # if wod_date.date().__eq__(today):
    # compare by day and month, while year on site is incorrect
    if wod_date.day.__eq__(today.day) and wod_date.month.__eq__(today.month):
        title = parser.get_wod_date()

        reg_part = parser.get_regional_wod()
        open_part = parser.get_open_wod()
        description = reg_part + "\n" + open_part

        reg_text = (''.join(reg_part.split())).lower()
        reg_text = reg_text[4:25]
        open_text = (''.join(open_part.split())).lower()
        open_text = open_text[4:25]

        if not reg_text.startswith("qualifierathletesrest") and not open_text.startswith("openathletesrest"):
            await wod_db.edit_wod(wod_id, today, title, description)

        return "Today's(" + today.strftime("%d %B %Y") + ") WOD successfully updated!"
    else:
        return "Error occurred while updating today's(" + today.strftime("%d %B %Y") + ") WOD!"


async def get_wod_old():
    today = datetime.now().date()

    result = await wod_db.get_wods(today)
    if result:
        wod_id = result[0].id
        title = result[0].title
        description = result[0].description

        return title + "\n\n" + description, wod_id

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
    # target = today.strftime("%m-%d-%y")
    target = f'{today.month}-{today.day}-{str(today.year)[-2:]}'
    base = os.environ['MAIN_URL']
    url = f'{base}/workout/{weekday.get(index)}-·-{target}'

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

        wod_id = None
        if not reg_text.startswith("regionalsathletesrest") and not open_text.startswith("openathletesrest"):
            wod_id = await wod_db.add_wod(today, title, description)

        return title + "\n\n" + description, wod_id
    except Exception as e:
        print(e)
        return "Комплекс еще не вышел.\nСорян :(", None