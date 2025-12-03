import sqlite3
import os

db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
print('DB path:', db)
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables before:', cur.fetchall())
try:
    cur.execute('DROP TABLE IF EXISTS recurring_booking')
    conn.commit()
    print('Dropped recurring_booking (if existed)')
except Exception as e:
    print('Error dropping:', e)
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables after:', cur.fetchall())
conn.close()