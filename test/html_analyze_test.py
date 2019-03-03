import codecs

from bs4 import BeautifulSoup

f = codecs.open("example03032019.html", 'r', 'utf-8')
soup = BeautifulSoup(f.read(), 'html.parser')

post = soup.find('div', class_='vc_gitem-zone-c')

h4 = post.find(class_='vc_gitem-post-data-source-post_title').find('h4').get_text()
wod_date = " ".join(h4.split())
content = post.find_all(class_='vc_col-sm-6')

result = ''
counter = 1

open_part = content[1].find(class_='wpb_wrapper').find(class_='wpb_wrapper')

for tag in open_part.find_all(["h2", "p"]):
    if tag.name == 'h2':
        # Remove unnecessary repeated spaces
        text = " ".join(tag.get_text().split())
        result += text + '\n\n'
    else:
        for inner in tag.find_all('strong'):
            print(inner)
            print(inner.get_text())
            # Add numbers for sections
            inner.string = f'{counter}. {inner.string}'
            counter += 1

        for link in tag.find_all('a'):
            link.string = link.get('href')

        for inner in tag.stripped_strings:
            # Remove unnecessary repeated spaces
            inner = " ".join(inner.split())
            result += inner + '\n'
        result += '\n'

# print(result)
