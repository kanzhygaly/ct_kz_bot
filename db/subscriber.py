from asyncpg_simpleorm import Column

from db.async_db import Entity


class Subscriber(Entity):
    __tablename__ = 'subscribers'

    user_id = Column()


async def add_subscriber(user_id):
    entity = Subscriber(user_id=user_id)
    await entity.save()


async def is_subscriber(user_id):
    return bool(await Subscriber.get_one(user_id=user_id))


async def unsubscribe(user_id):
    entity = Subscriber.get_one(user_id=user_id)
    await entity.delete()


async def get_all_subscribers():
    return await Subscriber.get(records=False)
