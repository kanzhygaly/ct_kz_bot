import os

from asyncpg_simpleorm import AsyncModel, Column, PoolManager

from db import db_utils

credentials = db_utils.database_url_parse(os.environ['DATABASE_URL'])

manager = PoolManager(
    user=credentials['user'],
    password=credentials['password'],
    host=credentials['host'],
    port=credentials['post'],
    database=credentials['database']
)


class AsyncDB(AsyncModel, connection=manager):
    id = Column()


async def drop_all_tables(connection) -> None:
    await connection.execute('''
            DROP TABLE IF EXISTS benchmark_result;
            DROP TABLE IF EXISTS benchmark_ru;
            DROP TABLE IF EXISTS benchmark;
            DROP TABLE IF EXISTS wod_result;
            DROP TABLE IF EXISTS wod_ru;
            DROP TABLE IF EXISTS wod;
            DROP TABLE IF EXISTS subscribers;
            DROP TABLE IF EXISTS users;
        ''')


async def create_all_tables(connection) -> None:
    await connection.execute('''
            CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY, user_id BIGINT,
            name VARCHAR(100), surname VARCHAR(100), lang VARCHAR(10));

            CREATE TABLE IF NOT EXISTS subscribers (id serial PRIMARY KEY, user_id BIGINT);

            CREATE TABLE IF NOT EXISTS wod (id serial PRIMARY KEY, wod_day date, title VARCHAR(150),
            description text);

            CREATE TABLE IF NOT EXISTS wod_ru (wod_id INTEGER not null, title VARCHAR(150),
            description text);

            CREATE TABLE IF NOT EXISTS wod_result (id serial PRIMARY KEY, wod_id INTEGER,
            user_id BIGINT, result VARCHAR(200), sys_date TIMESTAMP);

            CREATE TABLE IF NOT EXISTS benchmark (id serial PRIMARY KEY, title VARCHAR(150),
            description text, result_type VARCHAR(50));

            CREATE TABLE IF NOT EXISTS benchmark_ru (benchmark_id INTEGER not null,
            title VARCHAR(150), description text);

            CREATE TABLE IF NOT EXISTS benchmark_result (id serial PRIMARY KEY, benchmark_id INTEGER,
            wod_day date, user_id BIGINT, result VARCHAR(200), sys_date TIMESTAMP);
        ''')


class User(AsyncDB):
    __tablename__ = 'users'

    user_id = Column()
    name = Column()
    surname = Column()
    lang = Column()


async def add_user(user_id, name, surname, lang):
    entity = User(user_id=user_id, name=name, surname=surname, lang=lang)
    await entity.save()


async def is_user_exist(user_id):
    return bool(await User.get_one(user_id=user_id))


class Subscriber(AsyncDB):
    __tablename__ = 'subscribers'

    user_id = Column()


async def add_subscriber(user_id):
    entity = Subscriber(user_id=user_id)
    await entity.save()


async def is_subscriber(user_id):
    return bool(await Subscriber.get_one(user_id=user_id))


async def unsubscribe(user_id):
    entity = Subscriber.get_one(record=False, user_id=user_id)
    await entity.delete()


async def get_all_subscribers():
    return await Subscriber.get(records=False)


class WOD(AsyncDB):
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


class WodResult(AsyncDB):
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
