from asyncpg_simpleorm import Column

from db.async_db import Entity


class WOD(Entity):
    __tablename__ = 'wod'

    wod_day = Column()
    title = Column()
    description = Column()


async def get_wods(wod_day):
    return await WOD.get(records=False, wod_day=wod_day)


async def add_wod(wod_day, title, description):
    entity = WOD(wod_day=wod_day, title=title, description=description)
    await entity.save()
    return entity.id
