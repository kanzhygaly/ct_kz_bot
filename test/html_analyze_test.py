import codecs

from bs4 import BeautifulSoup

from utils.parser_util import parse_wod_content, parse_wod_date

f = codecs.open("example10072020.html", 'r', 'utf-8')
soup = BeautifulSoup(f.read(), 'html.parser')

post = soup.find('div', class_='wod-wrap aos-init aos-animate')

# header
header = post.find(class_='orange wod-date').find('h5').get_text()
wod_date = " ".join(header.split())
print(parse_wod_date(wod_date))
print(wod_date + '\n')

# wod content
content = post.find(class_='container wod-info').find_all(class_='col-md-6')

openResult = parse_wod_content(content[0])
print(openResult)

gamesResult = parse_wod_content(content[1])
print(gamesResult)
