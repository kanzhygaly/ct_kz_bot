import os

from asyncpg_simpleorm import PoolManager, Column, AsyncModel

from db import db_utils

credentials = db_utils.database_url_parse(os.environ['DATABASE_URL'])

manager = PoolManager(
    user=credentials['user'],
    password=credentials['password'],
    host=credentials['host'],
    port=credentials['post'],
    database=credentials['database']
)


class Entity(AsyncModel, connection=manager):
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

