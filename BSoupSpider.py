from bs4 import BeautifulSoup
import requests


class BSoupParser:

    def __init__(self):
        url = 'http://comptrain.co/individuals/home'
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')
        post = soup.find('div', class_='single-post')

        self.header = post.find(class_='header-container')
        self.content = post.find(class_='vc_row-fluid').find_all(class_='wpb_column')

    #@staticmethod
    def getWodDate(self):
        date = self.header.find('h1').get_text()
        return date

    def getRegionalWOD(self):
        reg_part = self.content[0].find(class_='wpb_wrapper')
        reg_title = reg_part.find('h3').get_text()
        print(reg_title)

        #regional = reg_part.find(class_='wpb_wrapper').find('div').get_text()
        for p in reg_part.find_all('p'):
            print(p.get_text())

        return reg_part.get_text()

    def getOpenWOD(self):
        open_part = self.content[1].find(class_='wpb_wrapper')
        open_title = open_part.find('h3').get_text()
        print(open_title)

        for p in open_part.find_all('p'):
            print(p.get_text())

        return open_part.get_text()
