from asyncpg_simpleorm import Column, select

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


async def get_user_wod_result(wod_id, user_id):
    async with WodResult.connection() as conn:
        async with conn.transaction():
            stmt = select(WodResult)
            where_str = 'SELECT wod_result.wod_id, wod_result.user_id, wod_result.result, wod_result.sys_date,' \
                        'wod_result.id FROM wod_result WHERE wod_result.wod_id = $1 AND wod_result.user_id = $2'
            args = (wod_id, user_id)
            stmt.set_statement('where', f'WHERE {where_str}', args)
            return await conn.fetchrow(*stmt)


async def get_one(_id):
    return await WodResult.get_one(record=False, id=_id)
