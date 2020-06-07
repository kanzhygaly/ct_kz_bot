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
        async with conn.transaction():
            col_str = "wod.id, wod.title"
            stmt = Statement(WOD)
            print(stmt)
            stmt.set_statement('from_', f'FROM {WOD.__tablename__}')
            print(stmt)
            stmt.set_statement('select', f'SELECT {col_str}')
            print(stmt)
            # stmt = select(WOD)
            where_str = "LOWER(wod.description) LIKE LOWER('%$1%')"
            stmt.set_statement('where', f'WHERE {where_str}', str)
            print(stmt)
            res = await conn.fetch(*stmt)
            print(res)
            return list(map(WOD.from_record, res))
