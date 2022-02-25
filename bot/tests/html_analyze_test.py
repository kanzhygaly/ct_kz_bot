import codecs

from bs4 import BeautifulSoup

from bot.util.parser_util import parse_wod_content, parse_wod_date, parse_wod_header

f = codecs.open("../resources/example24022022.html", 'r', 'utf-8')
soup = BeautifulSoup(f.read(), 'html.parser')

post = soup.find('div', id='wod')

wod_date = parse_wod_header(post)
print(parse_wod_date(wod_date))
print(wod_date + '\n')

wod_text = parse_wod_content(post)
print(wod_text)
