import codecs

from bs4 import BeautifulSoup

from bot.util.parser_util import parse_wod_content, parse_wod_date

f = codecs.open("../resources/example10072020.html", 'r', 'utf-8')
soup = BeautifulSoup(f.read(), 'html.parser')

post = soup.find('div', id='wod')

header = post.find('h5').get_text()
wod_date = " ".join(header.split())
print(parse_wod_date(wod_date))
print(wod_date + '\n')

wod_text = parse_wod_content(post)
print(wod_text)
