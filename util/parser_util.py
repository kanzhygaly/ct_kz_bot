from datetime import datetime

from constants.date_format import M_D_Y


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
            for inner in tag.find_all('em'):
                # remove <strong> in <em>
                inner.string = inner.get_text()

            for inner in tag.find_all('strong'):
                if not inner.get_text().split():
                    continue
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


def parse_wod_date(wod_string) -> datetime:
    wod_string = wod_string.replace('//', '').replace('/', '.')
    # Remove anything other than digits
    num = ''.join(c for c in wod_string if c.isdigit() or c == '.')
    return datetime.strptime(num, M_D_Y)
