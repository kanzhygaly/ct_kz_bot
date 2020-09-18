import datetime

from bot.constants import CMD_ADD_RESULT, CMD_VIEW_RESULTS
from bot.util.bsoup_spider import BSoupParser
from bot.util.parser_util import parse_wod_date

today = datetime.datetime.now().date()

url = 'https://comptrain.co/wod'
parser = BSoupParser(url=url)

title = parser.get_wod_date()
print(parse_wod_date(title))

open_part = parser.get_open_part()
reg_part = parser.get_games_part()

if reg_part.lower().find('rest day') != -1 and open_part.lower().find('rest day') != -1:
    print('Rest Day 1')
else:
    print('WOD 1')

if reg_part.lower().find('rest day') == -1 or open_part.lower().find('rest day') == -1:
    print('WOD 2')
else:
    print('Rest Day 2')

description = open_part + reg_part
msg = (f'/{CMD_ADD_RESULT} - записать/изменить результат за СЕГОДНЯ\n'
       f'/{CMD_VIEW_RESULTS} - посмотреть результаты за СЕГОДНЯ')
print(f'{title}\n\n{description}{msg}')
