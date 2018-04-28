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


content = post.find(class_='vc_row-fluid').find_all(class_='wpb_column')

reg_part = content[0].find(class_='wpb_wrapper')

reg_title = reg_part.find('h3').get_text()
print(reg_title)
# regional = reg_part.find(class_='wpb_wrapper').find('div').get_text()
for p in reg_part.find_all('p'):
    print(p.get_text())

open_part = content[1].find(class_='wpb_wrapper')

open_title = open_part.find('h3').get_text()
print(open_title)
for p in open_part.find_all('p'):
    print(p.get_text())
