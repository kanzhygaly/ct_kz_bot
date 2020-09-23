import os
import uuid
from datetime import datetime, date
from typing import Iterable

from bot.constants import CMD_VIEW_WOD, CMD_DISPATCH_WOD
from bot.service.info_service import get_wod_full_text
from bot.util.bsoup_spider import BSoupParser
from bot.constants.config_vars import WEB_URL
from bot.db import wod_db
from bot.exception import WodNotFoundError
from bot.util.parser_util import parse_wod_date


def dates_are_equal(date1: date, date2: date) -> bool:
    return date1.day == date2.day and date1.month == date2.month and date1.year == date2.year


def today_is_not_a_rest_day(parser: BSoupParser) -> bool:
    return (parser.get_games_part().lower().find('rest day') == -1
            and parser.get_open_part().lower().find('rest day') == -1)


async def get_today_wod():
    today = datetime.now().date()

    try:
        result = await wod_db.get_wod_by_date(today)
        return get_wod_full_text(header=result.title, body=result.description), result.id
    except WodNotFoundError:
        parser = BSoupParser(url=os.environ[WEB_URL])

        title = parser.get_wod_date()
        wod_date = parse_wod_date(title)

        if dates_are_equal(wod_date, today):
            description = parser.get_wod_text()

            wod_id = None
            if today_is_not_a_rest_day(parser):
                wod_id = await wod_db.add_wod(wod_day=today, title=title, description=description)

            return get_wod_full_text(header=title, body=description), wod_id
        else:
            return 'Комплекс еще не вышел.\nСорян :(', None


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
        return False, f'No resource found in DB use instead /{CMD_VIEW_WOD} and then /{CMD_DISPATCH_WOD}'

    parser = BSoupParser(url=os.environ[WEB_URL])

    title = parser.get_wod_date()
    wod_date = parse_wod_date(title)

    if dates_are_equal(wod_date, today):
        if today_is_not_a_rest_day(parser):
            await wod_db.edit_wod(id=wod_id, title=title, description=parser.get_wod_text())
            return True, ''

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
