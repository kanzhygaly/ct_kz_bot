import uuid

from asyncpg_simpleorm import Column, select, Statement

from db.async_db import Entity


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
        print(e)
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


async def get_wod_light(wod_id):
    async with WOD.connection() as conn:
        res = await conn.fetch(f'SELECT wod_day FROM {WOD.__tablename__} WHERE id={wod_id}')
        await conn.close()
        return WOD.from_record(res)


async def add_warmup(wod_id, txt):
    try:
        entity = await WOD.get_one(record=False, id=wod_id)
        entity.warmup = txt
        await entity.save()
        return entity.warmup
    except TypeError:
        return None
    except Exception as e:
        print(e)
        return None


async def get_warmup(wod_day):
    try:
        entity = await WOD.get_one(record=False, wod_day=wod_day)
        return entity.warmup
    except TypeError:
        return None
    except Exception as e:
        print(e)
        return None


async def search_by_text(str):
    async with WOD.connection() as conn:
        where_str = f'LOWER(description) LIKE LOWER(\'%{str}%\')'
        res = await conn.fetch(f'SELECT id, wod_day FROM {WOD.__tablename__} WHERE {where_str}')
        await conn.close()
        return list(map(WOD.from_record, res))

