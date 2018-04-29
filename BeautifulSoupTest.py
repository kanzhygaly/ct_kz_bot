import re
from bs4 import BeautifulSoup
import requests
import datetime

url = 'http://comptrain.co/individuals/home'
headers = {'User-Agent': 'Mozilla/5.0'}
page = requests.get(url, headers=headers)

soup = BeautifulSoup(page.text, 'html.parser')

post = soup.find('div', class_='single-post')

header = post.find(class_='header-container')

date = header.find('h1').get_text()
print(date)

# Remove anything other than digits
num = re.sub(r'\D', "", date)
date_wod = datetime.datetime.strptime(num, '%m%d%y')
print(date_wod.date())
now = datetime.datetime.now()
if date_wod.date().__eq__(now.date()):
    print('dates are identical')


content = post.find_all(class_='vc_col-sm-6')

reg_part = content[0].find(class_='wpb_wrapper')

reg_title = reg_part.find('h3')

if reg_title is not None:
    print(reg_title.get_text())

for p in reg_part.find_all('p'):
    print(p.get_text())

open_part = content[1].find(class_='wpb_wrapper')

open_title = open_part.find('h3')

if open_title is not None:
    print(open_title.get_text())

for p in open_part.find_all('p'):
    print(p.get_text())
