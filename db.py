import sqlite3
from datetime import datetime

class DB:
    def __init__(self, db_file):
        conn = sqlite3.connect(db_file, check_same_thread=False)
        self.conn = conn

    def get_connection(self):
        return self.conn

    def __del__(self):
        self.conn.close()


class PostsModel:
    def __init__(self, connection):
        self.connection = connection
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name='posts'")
        row = cursor.fetchone()
        if row is None:
            self.init_table()

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS posts
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             title VARCHAR(100),
                             path TEXT,
                             thmb_path TEXT,
                             user_id INTEGER,
                             pub_date INTEGER
                             )''')
        cursor.close()
        self.connection.commit()

    def insert(self, title, path, thmb_path, user_id):
        cursor = self.connection.cursor()
        pub_date = round(datetime.timestamp(datetime.now()))
        cursor.execute('''INSERT INTO posts
                          (title, path, thmb_path, user_id, pub_date)
                          VALUES (?,?,?,?,?)''', (title, path, thmb_path, str(user_id), pub_date))
        cursor.close()
        self.connection.commit()

    def get(self, post_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM posts WHERE id = ?", (str(post_id),))
        row = cursor.fetchone()
        return row

    def get_all(self, user_id=None):
        cursor = self.connection.cursor()
        if user_id:
            cursor.execute("SELECT * FROM posts WHERE user_id = ? ORDER BY pub_date DESC",
                           (str(user_id),))
        else:
            cursor.execute("SELECT * FROM posts ORDER BY pub_date DESC")
        rows = cursor.fetchall()
        return rows

    def delete(self, post_id):
        cursor = self.connection.cursor()
        cursor.execute('''DELETE FROM posts WHERE id = ?''', (str(post_id),))
        cursor.close()
        self.connection.commit()


class UsersModel:
    def __init__(self, connection):
        self.connection = connection
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name='users'")
        row = cursor.fetchone()
        if row is None:
            self.init_table()


    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             user_name VARCHAR(50),
                             password_hash VARCHAR(128),
                             admin INTEGER,
                             main_photo TEXT
                             )''')
        cursor.execute('''INSERT INTO users (user_name, password_hash, admin, main_photo)
                          VALUES (?,?,?,?)''', ('ermakova', 'pass', 0, 'no_photo.png'))
        cursor.execute('''INSERT INTO users (user_name, password_hash, admin, main_photo)
                          VALUES (?,?,?,?)''', ('avokamre', 'ssap', 0, 'no_photo.png'))
        cursor.execute('''INSERT INTO users (user_name, password_hash, admin, main_photo)
                          VALUES (?,?,?,?)''', ('ne_admin', 'ne_admin', 0, 'no_photo.png'))
        cursor.close()
        self.connection.commit()

    def insert(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute('''INSERT INTO users
                          (user_name, password_hash, admin, main_photo)
                          VALUES (?,?,?,?)''', (user_name, password_hash, 0, 'no_photo.png'))
        cursor.close()
        self.connection.commit()

    def get(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (str(user_id),))
        row = cursor.fetchone()
        return row

    def get_by_name(self, user_name):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ?", (user_name,))
        row = cursor.fetchone()
        return row

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return rows

    def exists(self, user_name, password_hash):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE user_name = ? AND password_hash = ?",
                       (user_name, password_hash))
        row = cursor.fetchone()
        return (True, row[0]) if row else (False,)


class SubsModel:
    def __init__(self, connection):
        self.connection = connection
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' and name='subscribers'")
        row = cursor.fetchone()
        if row is None:
            self.init_table()

    def init_table(self):
        cursor = self.connection.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS subscribers
                            (id INTEGER PRIMARY KEY AUTOINCREMENT,
                             subject INTEGER,
                             object INTEGER
                             )''')
        cursor.execute('''INSERT INTO subscribers (subject, object)
                                  VALUES (?, ?)''', (1, 2))
        cursor.execute('''INSERT INTO subscribers (subject, object)
                                  VALUES (?, ?)''', (1, 3))
        cursor.execute('''INSERT INTO subscribers (subject, object)
                                  VALUES (?, ?)''', (2, 3))
        cursor.close()
        self.connection.commit()

    def get_subscriptions(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT object FROM subscribers WHERE subject = ?", (user_id,))
        row = cursor.fetchall()
        return row

    def get_followers(self, user_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT subject FROM subscribers WHERE object = ?", (user_id,))
        row = cursor.fetchall()
        return row

