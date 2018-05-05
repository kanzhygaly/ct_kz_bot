import asyncpg_simpleorm as orm

from db.async_db import Entity


class WOD(Entity):
    __tablename__ = 'wod'
    return_records = False

    wod_day = orm.Column(orm.Date())
    title = orm.Column(orm.String(150))
    description = orm.Column(orm.String())


async def get_wods(wod_day):
    return await WOD.get(wod_day=wod_day)


async def add_wod(wod_day, title, description):
    entity = WOD(wod_day=wod_day, title=title, description=description)
    await entity.save()
    return entity.id
