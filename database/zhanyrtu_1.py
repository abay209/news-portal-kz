# zhanyrtu_1.py — 1-жаңарту: is_admin, facebook_id бағандары + bookmark, like кестелері
# Іске қосу: python database/zhanyrtu_1.py (proekt/ папкасынан)
# ⚠️ БІР РЕТ ҚАНА іске қос! Екі рет іске қосса қате шығуы мүмкін.

import sqlite3
import os

# Базаның жолы (proekt/ папкасында)
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'news_kz.db')

def migrate():
    if not os.path.exists(db_path):
        print(f"База табылмады: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        print("is_admin бағаны қосылды.")
    except sqlite3.OperationalError as e:
        print(f"is_admin бағаны бұрыннан бар: {e}")

    try:
        cursor.execute("ALTER TABLE user ADD COLUMN facebook_id VARCHAR(100)")
        print("facebook_id бағаны қосылды.")
    except sqlite3.OperationalError as e:
        print(f"facebook_id бағаны бұрыннан бар: {e}")

    # 1-пайдаланушыны admin ету
    cursor.execute("UPDATE user SET is_admin = 1 WHERE id = 1")

    # bookmark кестесін жасау
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookmark (
        id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        news_id INTEGER NOT NULL,
        created_at DATETIME,
        PRIMARY KEY (id),
        FOREIGN KEY(news_id) REFERENCES news (id),
        FOREIGN KEY(user_id) REFERENCES user (id)
    )
    ''')
    print("bookmark кестесі жасалды.")

    # like кестесін жасау
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "like" (
        id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        news_id INTEGER NOT NULL,
        created_at DATETIME,
        PRIMARY KEY (id),
        FOREIGN KEY(news_id) REFERENCES news (id),
        FOREIGN KEY(user_id) REFERENCES user (id)
    )
    ''')
    print("like кестесі жасалды.")

    conn.commit()
    conn.close()
    print("1-жаңарту сәтті аяқталды.")

if __name__ == '__main__':
    migrate()
