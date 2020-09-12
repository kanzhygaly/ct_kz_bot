import os
import uuid
from datetime import datetime, date
from typing import Iterable

from bsoup_spider import BSoupParser
from constants.config_vars import WEB_URL
from db import wod_db
from exception import WodNotFoundError
from util.parser_util import parse_wod_date


def the_wod_is_for_today(wod_date: date, today: date) -> bool:
    return wod_date.day == today.day and wod_date.month == today.month and wod_date.year == today.year


def today_is_not_a_rest_day(parser: BSoupParser) -> bool:
    return (parser.get_regional_wod().lower().find("rest day") == -1
            and parser.get_open_wod().lower().find("rest day") == -1)


async def get_today_wod():
    today = datetime.now().date()

    try:
        result = await wod_db.get_wod_by_date(today)
        wod_id = result.id
        title = result.title
        description = result.description

        return f'{title}\n\n{description}', wod_id
    except WodNotFoundError:
        parser = BSoupParser(url=os.environ[WEB_URL])

        wod_date = parse_wod_date(parser.get_wod_date())

        if the_wod_is_for_today(wod_date=wod_date, today=today):
            title = parser.get_wod_date()
            description = parser.get_regional_wod() + "\n" + parser.get_open_wod()

            wod_id = None
            if today_is_not_a_rest_day(parser):
                wod_id = await wod_db.add_wod(today, title, description)

            return f'{title}\n\n{description}', wod_id
        else:
            return "Комплекс еще не вышел.\nСорян :(", None


async def get_today_wod_id():
    today = datetime.now().date()
    try:
        result = await wod_db.get_wod_by_date(today)
        return result.id
    except WodNotFoundError as e:
        raise e


async def reset_today_wod() -> (bool, str):
    today = datetime.now().date()

    try:
        result = await wod_db.get_wod_by_date(today)
        wod_id = result.id
    except WodNotFoundError:
        return False, "No data found in DB use /sys_dispatch_wod instead"

    parser = BSoupParser(url=os.environ[WEB_URL])

    wod_date = parse_wod_date(parser.get_wod_date())

    if the_wod_is_for_today(wod_date=wod_date, today=today):
        if today_is_not_a_rest_day(parser):
            description = parser.get_regional_wod() + '\n' + parser.get_open_wod()
            await wod_db.edit_wod(id=wod_id, title=parser.get_wod_date(), description=description)
            return True

        return False, 'Today is a rest day!'
    else:
        return False, f'{today} is not equal to wod_date {wod_date}'


async def add_wod(wod_date: date, title: str, description: str = None):
    try:
        wod = await wod_db.get_wod_by_date(wod_date)
        await wod_db.edit_wod(id=wod.id, title=title, description=description)
        return wod.id
    except WodNotFoundError:
        return await wod_db.add_wod(wod_day=wod_date, title=title, description=description)


async def search_wod(text: str) -> Iterable[wod_db.WOD]:
    return await wod_db.search_by_text(text)


async def get_wod_by_str_id(wod_id_str: str):
    wod_id = uuid.UUID(wod_id_str)
    wod = await wod_db.get_wod(wod_id)
    return f'{wod.title}\n\n{wod.description}', wod_id
