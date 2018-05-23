import uuid

from asyncpg_simpleorm import Column

from db.async_db import Entity


class User(Entity):
    __tablename__ = 'users'

    id = Column(default=uuid.uuid4, primary_key=True)
    user_id = Column()
    name = Column()
    surname = Column()
    lang = Column()
    admin = Column()


async def add_user(user_id, name, surname, lang):
    entity = User(user_id=user_id, name=name, surname=surname, lang=lang)
    await entity.save()


async def is_user_exist(user_id):
    return bool(await User.get_one(user_id=user_id))


async def is_admin(user_id):
    return bool(await User.get_one(user_id=user_id, admin=True))


async def get_user(user_id):
    return await User.get_one(record=False, user_id=user_id)


async def get_all_users():
    return await User.get(records=False)
