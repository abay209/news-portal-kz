# zhanyrtu_2.py — 2-жаңарту: Source, Setting кестелері + бастапқы RSS дереккөздері
# Іске қосу: python database/zhanyrtu_2.py (proekt/ папкасынан)
# ⚠️ БІР РЕТ ҚАНА іске қос!

import sys
import os

# Жоғарыдағы папканы (proekt/) Python жолына қосу
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import Source, Setting

def migrate():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("База схемасы жаңартылды (жоқ кестелер жасалды).")

        # Бастапқы RSS дереккөздерін қосу
        if Source.query.count() == 0:
            initial_sources = [
                {'name': 'Tengrinews.kz', 'url': 'https://tengrinews.kz/news.rss', 'lang': 'ru'},
                {'name': 'Nur.kz', 'url': 'https://www.nur.kz/rss/', 'lang': 'ru'},
                {'name': 'Zakon.kz', 'url': 'https://www.zakon.kz/rss/', 'lang': 'ru'},
                {'name': 'Inform.kz', 'url': 'https://www.inform.kz/inform.rss', 'lang': 'ru'},
                {'name': 'BBC World', 'url': 'http://feeds.bbci.co.uk/news/world/rss.xml', 'lang': 'en'},
                {'name': 'The Verge', 'url': 'https://www.theverge.com/rss/index.xml', 'lang': 'en'},
                {'name': 'Motor1', 'url': 'https://www.motor1.com/rss/articles/all/', 'lang': 'en'}
            ]
            for s in initial_sources:
                new_source = Source(name=s['name'], url=s['url'], language=s['lang'])
                db.session.add(new_source)
            db.session.commit()
            print("Бастапқы RSS дереккөздері қосылды.")

if __name__ == "__main__":
    migrate()
