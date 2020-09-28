import os

from asyncpg_simpleorm import PoolManager, AsyncModel

from bot.constants.config_vars import DATABASE_URL
from bot.util.parser_util import database_url_parse

credentials = database_url_parse(os.environ[DATABASE_URL])

manager = PoolManager(
    user=credentials['user'],
    password=credentials['password'],
    host=credentials['host'],
    port=credentials['post'],
    database=credentials['database']
)


class Entity(AsyncModel, connection=manager):
    """
    Base Entity Class with ID column
    """


async def create_all_tables(connection) -> None:
    await connection.execute('''
            CREATE TABLE IF NOT EXISTS users (id uuid PRIMARY KEY, user_id BIGINT,
            name VARCHAR(100), surname VARCHAR(100), lang VARCHAR(10), admin BOOL DEFAULT false);

            CREATE TABLE IF NOT EXISTS subscribers (id uuid PRIMARY KEY, user_id BIGINT UNIQUE);

            CREATE TABLE IF NOT EXISTS wod (id uuid PRIMARY KEY, wod_day date, title VARCHAR(150),
            description TEXT, warmup TEXT);

            CREATE TABLE IF NOT EXISTS wod_result (id uuid PRIMARY KEY, wod_id uuid not null,
            user_id BIGINT, result TEXT, sys_date TIMESTAMP);

            CREATE TABLE IF NOT EXISTS benchmark (id uuid PRIMARY KEY, title VARCHAR(150),
            description TEXT, result_type VARCHAR(50));

            CREATE TABLE IF NOT EXISTS benchmark_result (id uuid PRIMARY KEY, benchmark_id uuid not null,
            wod_day date, user_id BIGINT, result VARCHAR(200), sys_date TIMESTAMP, link VARCHAR(100));
            
            CREATE TABLE IF NOT EXISTS location (user_id BIGINT PRIMARY KEY, longitude FLOAT,
            latitude FLOAT, locale VARCHAR(10), tz VARCHAR(200));
        ''')
