import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
print('DB path:', db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check if column already exists
cur.execute("PRAGMA table_info('booking')")
cols = [row[1] for row in cur.fetchall()]
print('Existing columns:', cols)
if 'recurring_booking_id' in cols:
    print('Column already exists, nothing to do.')
else:
    try:
        cur.execute('ALTER TABLE booking ADD COLUMN recurring_booking_id INTEGER')
        conn.commit()
        print('Column recurring_booking_id added successfully.')
    except Exception as e:
        print('Error adding column:', e)

conn.close()