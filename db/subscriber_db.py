import uuid
from typing import Iterable

from asyncpg_simpleorm import Column

from db.async_db import Entity


class Subscriber(Entity):
    __tablename__ = 'subscribers'

    id = Column(default=uuid.uuid4, primary_key=True)
    user_id = Column()


async def add_subscriber(user_id) -> None:
    entity = Subscriber(user_id=user_id)
    await entity.save()


async def is_subscriber(user_id) -> bool:
    return bool(await Subscriber.get_one(user_id=user_id))


async def unsubscribe(user_id) -> None:
    try:
        entity = await Subscriber.get_one(record=False, user_id=user_id)
        await entity.delete()
    except TypeError:
        print(f'Subscriber with user_id {user_id} was not found in DB')
    except Exception as e:
        print(e)


async def get_all_subscribers() -> Iterable[Subscriber]:
    return await Subscriber.get(records=False)
