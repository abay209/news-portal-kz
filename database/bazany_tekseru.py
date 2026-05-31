# bazany_tekseru.py — Базаның кестелерін және бағандарын экранға шығарады
# Іске қосу: python database/bazany_tekseru.py (proekt/ папкасынан)

import sqlite3
import os

# Базаның жолы (proekt/ папкасында)
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'news_kz.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print(f'Baza: {db_path}')
print('=' * 50)
print('Kesteler:')
for t in tables:
    print(f'  [keste] {t[0]}')
    cursor.execute(f"PRAGMA table_info({t[0]})")
    cols = cursor.fetchall()
    for col in cols:
        print(f'      - {col[1]} ({col[2]})')

conn.close()
