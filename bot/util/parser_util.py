from datetime import datetime, date
from typing import Dict

from bot.constants.date_format import M_D_Y


def parse_wod_content(content) -> str:
    result = ''
    counter = 1

    for tag in content.find_all(["h3", "h2", "p"]):
        if tag.name in ('h3', 'h2'):
            # Remove unnecessary repeated spaces
            text = " ".join(tag.get_text().split())
            if not text:
                continue
            result += text + '\n\n'
        else:
            # Enumerate section
            section_header = next(iter(tag.find_all(['strong', 'b'])), None)
            if section_header:
                section_header.string = f'{counter}. {section_header.get_text()}'
                counter += 1

            for link in tag.find_all('a'):
                link.string = link.get('href')

            for inner in tag.stripped_strings:
                # Remove unnecessary repeated spaces
                inner = " ".join(inner.split())
                result += inner + '\n'

            result += '\n'

    return result


def parse_wod_date(wod_string: str) -> date:
    wod_string = wod_string.replace('//', '').replace('/', '.')
    # Remove anything other than digits
    num = ''.join(c for c in wod_string if c.isdigit() or c == '.')
    return datetime.strptime(num, M_D_Y).date()


def database_url_parse(url: str) -> Dict[str, str]:
    url = url.replace('postgres://', '').replace('@', ' ').replace(':', ' ').replace('/', ' ').split()

    database_url = {}

    for part, credential in zip(range(len(url)), ['user', 'password', 'host', 'post', 'database']):
        database_url[credential] = url[part]

    return database_url


def valid_wod_result(wod_result_txt: str) -> bool:
    return sum(c.isdigit() for c in wod_result_txt) > 3
