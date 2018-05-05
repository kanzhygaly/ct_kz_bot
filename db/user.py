import asyncpg_simpleorm as orm

from db.async_db import Entity


class User(Entity):
    __tablename__ = 'users'
    return_records = False

    user_id = orm.Column(orm.BigInteger())
    name = orm.Column(orm.String(100))
    surname = orm.Column(orm.String(100))
    lang = orm.Column(orm.String(10))


async def add_user(user_id, name, surname, lang):
    entity = User(user_id=user_id, name=name, surname=surname, lang=lang)
    await entity.save()


async def is_user_exist(user_id):
    return bool(await User.get_one(user_id=user_id))
