import os
import uuid
from datetime import datetime, date
from typing import Iterable

from bsoup_spider import BSoupParser
from db import wod_db
from exception import WodNotFoundError
from util.parser_util import parse_wod_date


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


async def get_wod_id():
    today = datetime.now().date()
    result = await wod_db.get_wods(today)
    if result:
        return result[0].id


async def reset_wod():
    today = datetime.now().date()

    try:
        result = await wod_db.get_wod_by_date(today)
        wod_id = result.id
    except WodNotFoundError:
        return False, "No data found in DB use /sys_dispatch_wod instead"

    parser = BSoupParser(url=os.environ['WEB_URL'])

    wod_date = parse_wod_date(parser.get_wod_date())

    if (wod_date.day == today.day
            and wod_date.month == today.month
            and wod_date.year == today.year):

        reg_part = parser.get_regional_wod()
        open_part = parser.get_open_wod()

        if reg_part.find("Rest Day") == -1 or open_part.find("Rest Day") == -1:
            title = parser.get_wod_date()
            description = reg_part + "\n" + open_part
            await wod_db.edit_wod(id=wod_id, title=title, description=description)
            return True
        else:
            return False, "Today is the rest day!"
    else:
        return False, f"{today} is not equal to wod_date {wod_date}"


async def add_wod(wod_date: date, title: str, description: str = None):
    try:
        wod = await wod_db.get_wod_by_date(wod_date)
        await wod_db.edit_wod(id=wod.id, title=title, description=description)
        return wod.id
    except WodNotFoundError:
        return await wod_db.add_wod(wod_day=wod_date, title=title, description=description)


async def search_wod(text: str) -> Iterable[wod_db.WOD]:
    return await wod_db.search_by_text(text)


async def get_wod_by_str_id(wod_id_str):
    wod_id = uuid.UUID(wod_id_str)
    wod = await wod_db.get_wod(wod_id)
    return wod.title + "\n\n" + wod.description, wod_id
