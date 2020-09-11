import uuid
from datetime import date
from typing import Iterable

from asyncpg_simpleorm import Column

from db.async_db import Entity
from exception import WodNotFoundError


class WOD(Entity):
    __tablename__ = 'wod'

    id = Column(default=uuid.uuid4, primary_key=True)
    wod_day = Column()
    title = Column()
    description = Column()
    warmup = Column()


async def get_wods(wod_day):
    try:
        return await WOD.get(records=False, wod_day=wod_day)
    except TypeError as e:
        return None
    except Exception as e:
        print(e)
        return None


async def get_wod_by_date(wod_day):
    try:
        return await WOD.get_one(record=False, wod_day=wod_day)
    except TypeError:
        return None
    except Exception as e:
        print(e)
        return None


async def add_wod(wod_day, title, description):
    entity = WOD(wod_day=wod_day, title=title, description=description)
    await entity.save()
    return entity.id


async def edit_wod(id, description, title=None):
    try:
        entity = await WOD.get_one(record=False, id=id)
        entity.description = description

        if title:
            entity.title = title

        await entity.save()
        return entity
    except TypeError:
        return None
    except Exception as e:
        print(e)
        return None


async def get_wod(wod_id):
    try:
        return await WOD.get_one(record=False, id=wod_id)
    except TypeError:
        return None
    except Exception as e:
        print(e)
        return None


async def get_wod_day(wod_id):
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
        return entity.warmup
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
