import os
from pathlib import Path

from asyncpg_simpleorm import PoolManager, AsyncModel

from bot.constants.config_vars import ENV_DATABASE_URL, ENV_DB_SCRIPT
from bot.util.parser_util import database_url_parse

credentials = database_url_parse(os.environ[ENV_DATABASE_URL])

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
    p = Path('./bot/resources/db/create_all_tables.sql')
    if p.exists() and p.is_file():
        switch = os.environ[ENV_DB_SCRIPT]
        if switch and switch == 'enabled':
            await connection.execute(p.read_text())
