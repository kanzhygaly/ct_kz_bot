from datetime import datetime, date
from typing import Dict

from bot.constants.date_format import M_D_Y, M_D_sY


def remove_unnecessary_repeated_spaces(text: str) -> str:
    return ' '.join(text.split())


def remove_everything_but_digits(text: str) -> str:
    return ''.join(c for c in text if c.isdigit() or c == '.')


def convert_b_to_strong(tag) -> None:
    if (bold := tag.b) and bold.u:
        bold.name = "strong"

    if (underline := tag.u) and underline.b:
        underline.b.name = "strong"


def parse_wod_content(content) -> str:
    result = ''
    counter = 1

    for tag in content.find_all(["h3", "h2", "p"]):
        if tag.name in ('h3', 'h2'):
            if text := remove_unnecessary_repeated_spaces(tag.get_text()):
                result += text + '\n\n'
        else:
            convert_b_to_strong(tag)

            # Enumerate section header
            if section_header := tag.strong:
                section_header.string = f'{counter}. {section_header.get_text()}'
                counter += 1

            for link in tag.find_all('a'):
                link.string = link.get('href')

            for inner in tag.stripped_strings:
                result += remove_unnecessary_repeated_spaces(inner) + '\n'

            result += '\n'

    return result


def parse_wod_date(wod_date_str: str) -> date:
    wod_date_str = wod_date_str.replace('//', '').replace('/', '.')
    num = remove_everything_but_digits(wod_date_str)
    try:
        result = datetime.strptime(num, M_D_sY).date()
    except ValueError:
        result = datetime.strptime(num, M_D_Y).date()
    return result


def database_url_parse(url: str) -> Dict[str, str]:
    url = url.replace('postgres://', '').replace('@', ' ').replace(':', ' ').replace('/', ' ').split()

    database_url = {}

    for part, credential in zip(range(len(url)), ['user', 'password', 'host', 'post', 'database']):
        database_url[credential] = url[part]

    return database_url


def valid_wod_result(wod_result_txt: str) -> bool:
    return sum(c.isdigit() for c in wod_result_txt) > 3
