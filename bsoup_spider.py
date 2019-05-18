import requests
from bs4 import BeautifulSoup


class BSoupParser:
    def __init__(self, url):
        headers = {'User-Agent': 'Mozilla/5.0'}
        page = requests.get(url, headers=headers)

        soup = BeautifulSoup(page.text, 'html.parser')
        post = soup.find('div', class_='vc_gitem-zone-c')

        h4 = post.find(class_='vc_gitem-post-data-source-post_title').find('h4').get_text()
        self.wod_date = " ".join(h4.split())

        self.content = post.find_all(class_='vc_col-sm-6')

    def get_wod_date(self):
        return self.wod_date

    def get_regional_wod(self):
        result = ''
        counter = 1

        reg_part = self.content[0].find(class_='wpb_wrapper').find(class_='wpb_wrapper')

        for tag in reg_part.find_all(["h2", "p"]):
            if tag.name == 'h2':
                # Remove unnecessary repeated spaces
                text = " ".join(tag.get_text().split())
                result += text + '\n\n'
            else:
                for inner in tag.find_all('em'):
                    # remove <strong> in <em>
                    inner.string = inner.get_text()

                for inner in tag.find_all('strong'):
                    # Add numbers for sections
                    inner.string = f'{counter}. {inner.get_text()}'
                    counter += 1

                for link in tag.find_all('a'):
                    link.string = link.get('href')

                for inner in tag.stripped_strings:
                    # Remove unnecessary repeated spaces
                    inner = " ".join(inner.split())
                    result += inner + '\n'
                result += '\n'

        return result

    def get_open_wod(self):
        result = ''
        counter = 1

        open_part = self.content[1].find(class_='wpb_wrapper').find(class_='wpb_wrapper')

        for tag in open_part.find_all(["h2", "p"]):
            if tag.name == 'h2':
                # Remove unnecessary repeated spaces
                text = " ".join(tag.get_text().split())
                result += text + '\n\n'
            else:
                for inner in tag.find_all('em'):
                    # remove <strong> in <em>
                    inner.string = inner.get_text()

                for inner in tag.find_all('strong'):
                    # Add numbers for sections
                    inner.string = f'{counter}. {inner.get_text()}'
                    counter += 1

                for link in tag.find_all('a'):
                    link.string = link.get('href')

                for inner in tag.stripped_strings:
                    # Remove unnecessary repeated spaces
                    inner = " ".join(inner.split())
                    result += inner + '\n'
                result += '\n'

        return result
