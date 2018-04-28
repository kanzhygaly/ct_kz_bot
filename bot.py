import datetime
from BSoupSpider import BSoupParser
from BotHandler import BotHandler

greet_bot = BotHandler('552105148:AAH4hH232QZy7aOJ8IJyaXvc_L2Gq9t1Eh8')
greetings = ('здравствуй', 'привет', 'ку', 'здорово')
wod = ('что там сегодня', 'тренировка', 'треня', 'wod')
now = datetime.datetime.now()


def main():
    new_offset = None
    today = now.day

    while True:
        greet_bot.get_updates(new_offset)

        last_update = greet_bot.get_last_update()

        if last_update is not None:
            last_update_id = last_update['update_id']
            last_chat_text = last_update['message']['text']
            last_chat_id = last_update['message']['chat']['id']
            last_chat_name = last_update['message']['chat']['first_name']

            if last_chat_text.lower() in greetings and today == now.day and 6 <= now.hour < 12:
                greet_bot.send_message(last_chat_id, 'Доброе утро, {}'.format(last_chat_name))
                today += 1

            elif last_chat_text.lower() in greetings and today == now.day and 12 <= now.hour < 17:
                greet_bot.send_message(last_chat_id, 'Добрый день, {}'.format(last_chat_name))
                today += 1

            elif last_chat_text.lower() in greetings and today == now.day and 17 <= now.hour < 23:
                greet_bot.send_message(last_chat_id, 'Добрый вечер, {}'.format(last_chat_name))
                today += 1

            elif last_chat_text.lower() in wod:
                parser = BSoupParser()
                greet_bot.send_message(last_chat_id, parser.getWodDate()
                                       + parser.getRegionalWOD() + parser.getOpenWOD())

            new_offset = last_update_id + 1


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
