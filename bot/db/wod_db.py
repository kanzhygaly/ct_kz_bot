import uuid
from datetime import date
from typing import Iterable

from asyncpg_simpleorm import Column

from bot.db.async_db import Entity
from bot.exception import WodNotFoundError, ValueIsEmptyError


class WOD(Entity):
    __tablename__ = 'wod'

    id = Column(default=uuid.uuid4, primary_key=True)
    wod_day = Column()
    title = Column()
    description = Column()
    warmup = Column()


async def get_wod_list(wod_day: date) -> Iterable[WOD]:
    try:
        return await WOD.get(records=False, wod_day=wod_day)
    except TypeError:
        raise WodNotFoundError
    except Exception as e:
        print(e)
        raise WodNotFoundError


async def get_wod_by_date(wod_day: date) -> WOD:
    try:
        return await WOD.get_one(record=False, wod_day=wod_day)
    except TypeError:
        raise WodNotFoundError
    except Exception as e:
        print(e)
        raise WodNotFoundError


async def add_wod(wod_day: date, title: str, description: str = None):
    if description:
        entity = WOD(wod_day=wod_day, title=title, description=description)
    else:
        entity = WOD(wod_day=wod_day, title=title)
    await entity.save()
    return entity.id


async def edit_wod(id, title: str = None, description: str = None) -> WOD:
    try:
        entity = await WOD.get_one(record=False, id=id)

        if description:
            entity.description = description

        if title:
            entity.title = title

        await entity.save()
        return entity
    except TypeError:
        raise WodNotFoundError
    except Exception as e:
        print(e)
        raise WodNotFoundError


async def get_wod(wod_id) -> WOD:
    try:
        return await WOD.get_one(record=False, id=wod_id)
    except TypeError:
        raise WodNotFoundError
    except Exception as e:
        print(e)
        raise WodNotFoundError


async def get_wod_day(wod_id) -> date:
    async with WOD.connection() as conn:
        res = await conn.fetchval('SELECT wod_day FROM wod WHERE id = $1', wod_id)
        await conn.close()
        return res


async def add_warmup(wod_id, text: str) -> None:
    try:
        entity = await WOD.get_one(record=False, id=wod_id)
        entity.warmup = text
        await entity.save()
    except TypeError:
        raise WodNotFoundError
    except Exception as e:
        print(e)
        raise WodNotFoundError


async def get_warmup(wod_day: date) -> str:
    try:
        entity = await WOD.get_one(record=False, wod_day=wod_day)
        warmup = entity.warmup
        if warmup:
            return warmup

        raise ValueIsEmptyError
    except TypeError:
        raise WodNotFoundError
    except Exception as e:
        print(e)
        raise WodNotFoundError


async def search_by_text(text: str) -> Iterable[WOD]:
    async with WOD.connection() as conn:
        where_str = f'LOWER(description) LIKE LOWER(\'%{text}%\')'
        res = await conn.fetch(f'SELECT id, wod_day FROM {WOD.__tablename__} WHERE {where_str}')
        await conn.close()
        return list(map(WOD.from_record, res))
