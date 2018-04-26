import datetime
from BotHandler import BotHandler
from FeedHandler import FeedHandler

greet_bot = BotHandler('552105148:AAH4hH232QZy7aOJ8IJyaXvc_L2Gq9t1Eh8')
greetings = ('здравствуй', 'привет', 'ку', 'здорово')
wod = ('что там сегодня', 'тренировка', 'треня', 'wod')
now = datetime.datetime.now()


def main():
    new_offset = None
    today = now.day
    hour = now.hour

    while True:
        greet_bot.get_updates(new_offset)

        last_update = greet_bot.get_last_update()

        if last_update is not None:
            last_update_id = last_update['update_id']
            last_chat_text = last_update['message']['text']
            last_chat_id = last_update['message']['chat']['id']
            last_chat_name = last_update['message']['chat']['first_name']

            if last_chat_text.lower() in greetings and today == now.day and 6 <= hour < 12:
                greet_bot.send_message(last_chat_id, 'Доброе утро, {}'.format(last_chat_name))
                today += 1

            elif last_chat_text.lower() in greetings and today == now.day and 12 <= hour < 17:
                greet_bot.send_message(last_chat_id, 'Добрый день, {}'.format(last_chat_name))
                today += 1

            elif last_chat_text.lower() in greetings and today == now.day and 17 <= hour < 23:
                greet_bot.send_message(last_chat_id, 'Добрый вечер, {}'.format(last_chat_name))
                today += 1

            elif last_chat_text.lower() in wod:
                url = 'http://comptrain.co/individuals/home/'

                # Check if argument matches url format
                if not FeedHandler.is_parsable(url):
                    message = "Sorry! It seems like '" + str(url) + "' doesn't provide an RSS news feed.. Have you " \
                                                                    "tried another URL from that provider? "
                    greet_bot.send_message(last_chat_id, message)
                    return

                args_count = 4

                entries = FeedHandler.parse_feed(url, args_count)
                for entry in entries:
                    message = "[" + url[1] + "] <a href='" + \
                              entry.link + "'>" + entry.title + "</a>"
                    print(message)

            new_offset = last_update_id + 1


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
