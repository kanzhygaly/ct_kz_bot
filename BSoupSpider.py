from bs4 import BeautifulSoup
import requests


class BSoupParser:

    def __init__(self):
        url = 'http://comptrain.co/individuals/home'
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')
        post = soup.find('div', class_='single-post')

        self.wod_date = post.find(class_='header-container').find('h1').get_text()

        self.content = post.find_all(class_='vc_col-sm-6')

    def get_wod_date(self):
        return self.wod_date

    def get_regional_wod(self):
        result = ''

        reg_part = self.content[0].find(class_='wpb_wrapper')
        title = reg_part.find('h3').get_text()
        result += title + '\n'

        for p in reg_part.find_all('p'):
            result += p.get_text() + "\n\n"

        # return reg_part.get_text()
        return result

    def get_open_wod(self):
        result = ''

        open_part = self.content[1].find(class_='wpb_wrapper')
        title = open_part.find('h3').get_text()
        result += title + '\n'

        for p in open_part.find_all('p'):
            result += p.get_text() + "\n\n"

        # return reg_part.get_text()
        return result
