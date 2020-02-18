import os
import pytz
from datetime import datetime
from bsoup_spider import BSoupParser
from db import user_db, wod_db, wod_result_db, location_db
from utils.parser_util import parse_wod_date


async def get_wod():
    today = datetime.now().date()

    result = await wod_db.get_wods(today)
    if result:
        wod_id = result[0].id
        title = result[0].title
        description = result[0].description

        return title + "\n\n" + description, wod_id

    parser = BSoupParser(url=os.environ['WEB_URL'])

    wod_date = parse_wod_date(parser.get_wod_date())

    if wod_date.day.__eq__(today.day) and wod_date.month.__eq__(today.month) and wod_date.year.__eq__(today.year):
        title = parser.get_wod_date()

        reg_part = parser.get_regional_wod()
        open_part = parser.get_open_wod()
        description = reg_part + "\n" + open_part

        if reg_part.find("Rest Day") != -1 or open_part.find("Rest Day") != -1:
            wod_id = None
        else:
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

        # replace * with x in text. if it has odd number of * then MARKDOWN will fail
        msg = msg.replace('*','x')

        return msg
    else:
        return None


async def reset_wod():
    today = datetime.now().date()

    result = await wod_db.get_wod_by_date(today)
    wod_id = result.id

    parser = BSoupParser(url=os.environ['WEB_URL'])

    wod_date = parse_wod_date(parser.get_wod_date())

    # compare by day and month, while year on site is incorrect
    if wod_date.day.__eq__(today.day) and wod_date.month.__eq__(today.month):
        reg_part = parser.get_regional_wod()
        open_part = parser.get_open_wod()

        if reg_part.find("Rest Day") == -1 or open_part.find("Rest Day") == -1:
            title = parser.get_wod_date()
            description = reg_part + "\n" + open_part
            await wod_db.edit_wod(id=wod_id, description=description, title=title)
            return True
        else:
            print("Today is the rest day!")
            return False
    else:
        return False


async def add_wod(wod_date, title, description):
    wod = await wod_db.get_wod_by_date(wod_date)
    if wod:
        await wod_db.edit_wod(id=wod.id, description=description, title=title)
        return wod.id
    else:
        return await wod_db.add_wod(wod_date, title, description)
