import codecs

from bs4 import BeautifulSoup


f = codecs.open("example.html", 'r', 'utf-8')
soup = BeautifulSoup(f.read(), 'html.parser')

post = soup.find('div', class_='single-post')
wod_date = post.find(class_='header-container').find('h1').get_text()
content = post.find_all(class_='vc_col-sm-6')

reg_part = content[0].find(class_='wpb_wrapper').find(class_='wpb_wrapper')

result = ''
for tag in reg_part.find_all(["h3", "p"]):
    if tag.name == 'h3':
        result += tag.get_text().strip() + '\n'
    else:
        result += tag.get_text().strip() + '\n\n'
print(result)
# for child in reg_part.children:
#     print(child.string)
# print(str(reg_part.get_text()).strip())

# OPEN
open_part = content[1].find(class_='wpb_wrapper').find(class_='wpb_wrapper')
title = open_part.find('h3').get_text()
print(title)

result = ''
sections = list(line.get_text() for line in open_part.find_all('p'))

for section in sections:
    result += section + '\n\n'
    for line in section.splitlines():
        if line:
            print(line + '[]')

