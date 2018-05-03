import os

import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']


class Database:

    def __init__(self):
        self.connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        self.cursor = self.connection.cursor()

    def init_tables(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS users (id serial PRIMARY KEY, user_id BIGINT,"
                            "name VARCHAR(100), surname VARCHAR(100), lang VARCHAR(10));")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS subscribers (id serial PRIMARY KEY, user_id BIGINT);")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS wod (id serial PRIMARY KEY, wod_day date, title VARCHAR(150),"
                            "description text);")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS wod_ru (wod_id INTEGER not null, title VARCHAR(150),"
                            "description text);")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS wod_result (id serial PRIMARY KEY, wod_id INTEGER,"
                            "user_id BIGINT, result VARCHAR(200), sys_date TIMESTAMP);")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS benchmark (id serial PRIMARY KEY, title VARCHAR(150),"
                            "description text, result_type VARCHAR(50));")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS benchmark_ru (benchmark_id INTEGER not null,"
                            "title VARCHAR(150), description text);")

        self.cursor.execute("CREATE TABLE IF NOT EXISTS benchmark_result (id serial PRIMARY KEY, benchmark_id INTEGER,"
                            "wod_day date, user_id BIGINT, result VARCHAR(200), sys_date TIMESTAMP);")

        self.connection.commit()

    def add_user(self, user_id, name, surname, lang):
        self.cursor.execute("INSERT INTO users (user_id, name, surname, lang) VALUES (%s, %s, %s, %s)",
                            (user_id, name, surname, lang))
        self.connection.commit()

    def is_user_exist(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        return bool(self.cursor.fetchone())

    def add_subscriber(self, user_id):
        self.cursor.execute("INSERT INTO subscribers (user_id) VALUES (%s)", (user_id,))
        self.connection.commit()

    def is_subscriber(self, user_id):
        self.cursor.execute("SELECT * FROM subscribers WHERE user_id=%s", (user_id,))
        return bool(self.cursor.fetchone())

    def unsubscribe(self, user_id):
        self.cursor.execute("DELETE FROM subscribers WHERE user_id=%s", (user_id,))

    def get_all_subscribers(self):
        self.cursor.execute("SELECT * FROM subscribers")
        return list(set([column[1] for column in self.cursor]))

    def get_wods(self, wod_day):
        self.cursor.execute("SELECT * FROM wod WHERE wod_day=%s", (wod_day,))

        wod, list_res = {}, {}
        i = 0

        for column in self.cursor:
            wod['id'] = column[0]
            wod['title'] = column[2]
            wod['description'] = column[3]

            list_res[i] = wod
            wod = {}
            i += 1

        return list_res

    def add_wod(self, wod_day, title, description):
        self.cursor.execute("INSERT INTO wod (wod_day, title, description) VALUES (%s, %s, %s) RETURNING id",
                            (wod_day, title, description))
        wod_id = self.cursor.fetchone()[0]
        self.connection.commit()
        return wod_id

    def get_wod_results(self, wod_id):
        self.cursor.execute("SELECT * FROM wod_result WHERE wod_id=%s", (wod_id,))

        wod_result, list_res = {}, {}
        i = 0

        for column in self.cursor:
            wod_result['id'] = column[0]
            wod_result['wod_id'] = column[1]
            wod_result['user_id'] = column[2]
            wod_result['result'] = column[3]
            wod_result['sys_date'] = column[4]

            list_res[i] = wod_result
            wod_result = {}
            i += 1

        return list_res

    def add_wod_result(self, wod_id, user_id, result, sys_date):
        self.cursor.execute("INSERT INTO wod_result (wod_id, user_id, result, sys_date) VALUES (%s, %s, %s, %s)",
                            (wod_id, user_id, result, sys_date))
        self.connection.commit()
