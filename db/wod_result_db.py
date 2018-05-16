from asyncpg_simpleorm import Column

from db.async_db import Entity


class WodResult(Entity):
    __tablename__ = 'wod_result'

    wod_id = Column()
    user_id = Column()
    result = Column()
    sys_date = Column()


async def get_wod_results(wod_id):
    return await WodResult.get(records=False, wod_id=wod_id)


async def add_wod_result(wod_id, user_id, result, sys_date):
    entity = WodResult(wod_id=wod_id, user_id=user_id, result=result, sys_date=sys_date)
    await entity.save()


async def get_wod_result(wod_id, user_id):
    return await WodResult.get(record=False, wod_id=wod_id, user_id=user_id)[0]


async def get_one(_id):
    return await WodResult.get_one(record=False, id=_id)
