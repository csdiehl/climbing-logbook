import sqlite3

conn = sqlite3.connect('climbs.db')
print("opened database connection")

conn.execute('CREATE TABLE users (username TEXT UNIQUE, user_id INTEGER PRIMARY KEY) ')
print("user table added")

conn.execute('CREATE TABLE indoor (user_id INTEGER NOT NULL, date TEXT, grade TEXT, type TEXT, num_routes INTEGER, send_type TEXT, FOREIGN KEY (user_id) REFERENCES users (user_id))')
print("log table added")

conn.execute('CREATE TABLE outdoor (user_id INTEGER NOT NULL, date TEXT, grade TEXT, name TEXT, location TEXT, height INTEGER, pitches INTEGER, FOREIGN KEY (user_id) REFERENCES users (user_id))')

conn.close()

#CREATE TABLE outdoor2 (user_id INTEGER NOT NULL, date TEXT, grade TEXT, name TEXT, location TEXT, height INTEGER, pitches INTEGER, type TEXT, send_type TEXT, row_id INTEGER PRIMARY KEY, FOREIGN KEY (user_id) REFERENCES users (user_id))