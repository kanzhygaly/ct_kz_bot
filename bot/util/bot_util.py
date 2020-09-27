from datetime import date

from aiogram import types
from aiogram.dispatcher import FSMContext

from bot.constants import WOD_STR
from bot.constants.config_vars import BOT_NAME
from bot.exception import WodDateNotFoundError
from bot.util.parser_util import parse_wod_date


def handle_reply_to_wod_msg(message: types.Message) -> date:
    reply_to_msg = message.reply_to_message
    if reply_to_msg and reply_to_msg.from_user.is_bot and reply_to_msg.from_user.username == BOT_NAME:
        first_line = str(reply_to_msg.text).split('\n', 1)[0]
        if first_line.startswith(WOD_STR):
            return parse_wod_date(first_line)

    raise WodDateNotFoundError


def rest_day(date_to_check: date) -> bool:
    return date_to_check.weekday() in (3, 6) or False


async def reset_state(state: FSMContext) -> None:
    await state.reset_state()
    await state.update_data(wod_id=None)
    await state.update_data(wod_result_id=None)
    await state.update_data(wod_result_txt=None)
    await state.update_data(view_wod_id=None)
