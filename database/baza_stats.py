import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'news_kz.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM news")
total = c.fetchone()[0]
print(f"Barlyk zhanaly_k sany: {total}")

c.execute("SELECT COUNT(*) FROM news WHERE created_at >= date('now', '-7 days')")
week = c.fetchone()[0]
print(f"Songgy 7 kunde qosylgan: {week}")

c.execute("SELECT COUNT(*) FROM news WHERE created_at >= date('now', '-1 days')")
today = c.fetchone()[0]
print(f"Bugyn qosylgan: {today}")

c.execute("SELECT source_name, COUNT(*) as cnt FROM news GROUP BY source_name ORDER BY cnt DESC LIMIT 8")
print("\nDerekkoz boyynsha:")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]} zhanalyk")

c.execute("SELECT title_ru, created_at FROM news ORDER BY created_at DESC LIMIT 5")
print("\nEn songgy 5 zhanalyk:")
for r in c.fetchall():
    title = r[0][:60] + '...' if r[0] and len(r[0]) > 60 else r[0]
    print(f"  [{r[1]}] {title}")

conn.close()
