from asyncpg_simpleorm import Column

from bot.db.async_db import Entity
from bot.exception import LocationNotFoundError


class Location(Entity):
    __tablename__ = 'location'

    user_id = Column(primary_key=True)
    longitude = Column()
    latitude = Column()
    locale = Column()
    tz = Column()


async def add_location(user_id, longitude: float, latitude: float, locale: str, timezone: str) -> None:
    entity = Location(user_id=user_id, longitude=longitude, latitude=latitude, locale=locale, tz=timezone)
    await entity.save()


async def get_location(user_id) -> Location:
    try:
        return await Location.get_one(record=False, user_id=user_id)
    except TypeError:
        raise LocationNotFoundError
    except Exception as e:
        print(e)
        raise LocationNotFoundError
