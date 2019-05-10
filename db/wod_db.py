import uuid

from asyncpg_simpleorm import Column

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
