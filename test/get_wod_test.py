import datetime

from bsoup_spider import BSoupParser

today = datetime.datetime.now().date()

url = 'https://comptrain.co/individuals/programming'
parser = BSoupParser(url=url)

# Remove anything other than digits
# num = re.sub(r'\D', "", parser.get_wod_date())
num = ''.join(c for c in parser.get_wod_date() if c.isdigit() or c == '.')
wod_date = datetime.datetime.strptime(num, '%m.%d.%Y')

# if wod_date.date().__eq__(today):
if wod_date.day.__eq__(today.day) and wod_date.month.__eq__(today.month) and wod_date.year.__eq__(today.year):
    title = parser.get_wod_date()
    reg_part = parser.get_regional_wod()
    open_part = parser.get_open_wod()
    description = reg_part + "\n" + open_part

    reg_text = (''.join(reg_part.split())).lower()
    reg_text = reg_text[:25]
    open_text = (''.join(open_part.split())).lower()
    open_text = open_text[:20]

    # if reg_text == "qualifierathletesrest" and open_text == "openathletesrest":
    if reg_part.find("Rest Day") != -1 or open_part.find("Rest Day") != -1:
        print("NO DB")
        print(title + "\n\n" + description)
    else:
        print("SAVE TO DB")
        print(title + "\n\n" + description)
else:
    print("Комплекс еще не вышел.\nСорян :(")

