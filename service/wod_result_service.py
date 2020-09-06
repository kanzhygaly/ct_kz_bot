import pytz
from datetime import datetime
from db import user_db, wod_result_db, location_db


async def get_wod_results(user_id, wod_id):
    location = await location_db.get_location(user_id)

    wod_results = await wod_result_db.get_wod_results(wod_id)

    if wod_results:
        msg = ''
        for res in wod_results:
            u = await user_db.get_user(res.user_id)

            dt = res.sys_date.astimezone(pytz.timezone(location.tz)) if location else res.sys_date
            name = f'{u.name} {u.surname}' if u.surname else u.name

            title = '_' + name + ', ' + dt.strftime("%H:%M:%S %d %B %Y") + '_'
            msg += f'{title}\n' \
                   f'{res.result}\n\n'

        # replace * with x in text. if it has odd number of * then MARKDOWN will fail
        msg = msg.replace('*', 'x')

        return msg
    else:
        return None


async def is_allowed_to_see_wod_results(user_id):
    wod_result = await wod_result_db.get_last_wod_result(user_id)

    if wod_result:
        delta = datetime.now() - wod_result.sys_date
        if delta.days > 3:
            # if user hasn't logged any results within 3 days
            # then he is not allowed to see results
            return False
        else:
            # allowed to see results
            return True
    else:
        # no results at all, not allowed
        return False
