import os
import uuid

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
    _id = Column(key='id', default=uuid.uuid4, primary_key=True)


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
            CREATE TABLE IF NOT EXISTS users (id uuid PRIMARY KEY, user_id BIGINT,
            name VARCHAR(100), surname VARCHAR(100), lang VARCHAR(10), admin BOOL DEFAULT false);

            CREATE TABLE IF NOT EXISTS subscribers (id uuid PRIMARY KEY, user_id BIGINT);

            CREATE TABLE IF NOT EXISTS wod (id uuid PRIMARY KEY, wod_day date, title VARCHAR(150),
            description text);

            CREATE TABLE IF NOT EXISTS wod_ru (wod_id uuid not null, title VARCHAR(150),
            description text);

            CREATE TABLE IF NOT EXISTS wod_result (id uuid PRIMARY KEY, wod_id uuid not null,
            user_id BIGINT, result VARCHAR(200), sys_date TIMESTAMP);

            CREATE TABLE IF NOT EXISTS benchmark (id uuid PRIMARY KEY, title VARCHAR(150),
            description text, result_type VARCHAR(50));

            CREATE TABLE IF NOT EXISTS benchmark_ru (benchmark_id uuid not null,
            title VARCHAR(150), description text);

            CREATE TABLE IF NOT EXISTS benchmark_result (id uuid PRIMARY KEY, benchmark_id uuid not null,
            wod_day date, user_id BIGINT, result VARCHAR(200), sys_date TIMESTAMP);
        ''')

