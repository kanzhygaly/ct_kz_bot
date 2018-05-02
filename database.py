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

        self.cursor.execute("CREATE TABLE IF NOT EXISTS wod (id serial PRIMARY KEY, wod_date date, title VARCHAR(150),"
                            "description text, result VARCHAR(150), user_id BIGINT);")

        self.connection.commit()

    def add_user(self, user_id, name, surname, lang):
        self.cursor.execute("INSERT INTO users (user_id, name, surname, lang) VALUES (%d, %s, %s, %s)",
                            (user_id, name, surname, lang))
        self.connection.commit()

    def is_user_exist(self, user_id):
        self.cursor.execute("SELECT * FROM users WHERE user_id=%d", (user_id,))
        return bool(self.cursor.fetchone())

    def add_subscriber(self, user_id):
        self.cursor.execute("INSERT INTO subscribers (user_id) VALUES (%d)", (user_id,))
        self.connection.commit()

    def is_subscriber(self, user_id):
        self.cursor.execute("SELECT * FROM subscribers WHERE user_id=%d", (user_id,))
        return bool(self.cursor.fetchone())

    def unsubscribe(self, user_id):
        self.cursor.execute("DELETE FROM subscribers WHERE user_id=%d", (user_id,))

    def get_all_subscribers(self):
        self.cursor.execute("SELECT * FROM subscribers")
        return list(set([column[2] for column in self.cursor]))
