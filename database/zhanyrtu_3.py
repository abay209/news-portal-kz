# zhanyrtu_3.py — 3-жаңарту: User кестесіне email/phone/google_id/avatar + comment кестесі
# Іске қосу: python database/zhanyrtu_3.py (proekt/ папкасынан)
# ⚠️ БІР РЕТ ҚАНА іске қос!

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

    print("User кестесі жаңартылуда...")
    try:
        cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(120)")
        cursor.execute("CREATE UNIQUE INDEX ix_user_email ON user(email)")
        cursor.execute("ALTER TABLE user ADD COLUMN phone_number VARCHAR(20)")
        cursor.execute("CREATE UNIQUE INDEX ix_user_phone_number ON user(phone_number)")
        cursor.execute("ALTER TABLE user ADD COLUMN google_id VARCHAR(100)")
        cursor.execute("CREATE UNIQUE INDEX ix_user_google_id ON user(google_id)")
        cursor.execute("ALTER TABLE user ADD COLUMN avatar_url VARCHAR(300)")
        cursor.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
        cursor.execute("UPDATE user SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        print("User кестесіне жаңа бағандар қосылды.")
    except sqlite3.OperationalError as e:
        print(f"User кестесі ескертуі: {e}")

    print("comment кестесі жасалуда...")
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            news_id INTEGER NOT NULL,
            guest_name VARCHAR(100),
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(news_id) REFERENCES news(id)
        )
        """)
        print("comment кестесі жасалды.")
    except sqlite3.OperationalError as e:
        print(f"comment кестесі ескертуі: {e}")

    conn.commit()
    conn.close()
    print("3-жаңарту сәтті аяқталды.")

if __name__ == "__main__":
    migrate()
