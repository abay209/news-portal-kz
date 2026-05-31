# zhanyrtu_ai.py — AI жаңартуы: news кестесіне summary_ru/kk/en бағандары
# Іске қосу: python database/zhanyrtu_ai.py (proekt/ папкасынан)
# ⚠️ БІР РЕТ ҚАНА іске қос!

import sqlite3
import os

# Базаның жолы (proekt/ папкасында)
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'news_kz.db')

def upgrade():
    if not os.path.exists(db_path):
        print(f"Қате: База табылмады — {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("AI жаңартуы басталуда...")

        try:
            cursor.execute("ALTER TABLE news ADD COLUMN summary_ru TEXT;")
            print("summary_ru бағаны қосылды.")
        except sqlite3.OperationalError:
            print("summary_ru бағаны бұрыннан бар.")

        try:
            cursor.execute("ALTER TABLE news ADD COLUMN summary_kk TEXT;")
            print("summary_kk бағаны қосылды.")
        except sqlite3.OperationalError:
            print("summary_kk бағаны бұрыннан бар.")

        try:
            cursor.execute("ALTER TABLE news ADD COLUMN summary_en TEXT;")
            print("summary_en бағаны қосылды.")
        except sqlite3.OperationalError:
            print("summary_en бағаны бұрыннан бар.")

        conn.commit()
        print("AI жаңартуы сәтті аяқталды.")
    except Exception as e:
        print(f"Жаңарту кезінде қате: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    upgrade()
