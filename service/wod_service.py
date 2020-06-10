import os
import uuid
from datetime import datetime
from bsoup_spider import BSoupParser
from db import wod_db
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

        if reg_part.lower().find("rest day") != -1 and open_part.lower().find("rest day") != -1:
            # Rest Day on both parts
            wod_id = None
        else:
            wod_id = await wod_db.add_wod(today, title, description)

        return title + "\n\n" + description, wod_id
    else:
        return "Комплекс еще не вышел.\nСорян :(", None


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


async def search_wods(str):
    return await wod_db.search_by_text(str)


async def get_wod_by_str_id(wod_id_str):
    print(wod_id_str)
    wod_id = uuid.UUID(bytes=wod_id_str.bytes)
    print(wod_id)
    wod = await wod_db.get_wod(wod_id)
    return wod.title + "\n\n" + wod.description, wod_id
