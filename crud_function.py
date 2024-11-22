import sqlite3


# Функция для инициализации базы данных
def initiate_db(db_name='database.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Создание таблицы Users, если она не существует
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        age INTEGER NOT NULL,
        balance INTEGER NOT NULL DEFAULT 1000
    )
    ''')

    conn.commit()
    conn.close()


# Функция для добавления пользователя
def add_user(username, email, age, db_name='database.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('''
    INSERT INTO Users (username, email, age, balance) 
    VALUES (?, ?, ?, ?)
    ''', (username, email, age, 1000))

    conn.commit()
    conn.close()


# Функция для проверки существования пользователя
def is_included(username, db_name='database.db'):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Users WHERE username = ?', (username,))
    user = cursor.fetchone()

    conn.close()
    return user is not None
