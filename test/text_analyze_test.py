import codecs

from bs4 import BeautifulSoup


f = codecs.open("example_21112018.html", 'r', 'utf-8')
soup = BeautifulSoup(f.read(), 'html.parser')

post = soup.find('div', class_='vc_gitem-zone-c')

wod_date = post.find(class_='vc_gitem-post-data-source-post_title').find('h4').get_text()
wod_date = " ".join(wod_date.split())
print(wod_date)

content = post.find_all(class_='vc_col-sm-6')

reg_part = content[0].find(class_='wpb_wrapper').find(class_='wpb_wrapper')

result = ''
counter = 1
for tag in reg_part.find_all(["h2", "p"]):
    if tag.name == 'h2':
        text = " ".join(tag.get_text().split())
        result += text + '\n\n'
    else:
        for inner in tag.find_all('strong'):
            inner.string = f'{counter}. {inner.string}'
            counter += 1

        for inner in tag.stripped_strings:
            inner = " ".join(inner.split())
            result += inner + '\n'
        result += '\n'

print(result)
# for child in reg_part.children:
#     print(child.string)
# print(str(reg_part.get_text()).strip())

# OPEN
open_part = content[1].find(class_='wpb_wrapper').find(class_='wpb_wrapper')
title = open_part.find('h2').get_text()
title = " ".join(title.split())
print(title)

result = ''
sections = list(line.get_text() for line in open_part.find_all('p'))

for section in sections:
    # result += section + '\n\n'
    for line in section.splitlines():
        text = " ".join(line.split())
        print(text)
        # if line:

