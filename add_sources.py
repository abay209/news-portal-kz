import os
from app import create_app, db
from app.models import Source

sources = [
    # Politics
    {'name': 'Zakon.kz', 'url': 'https://www.zakon.kz/rss.xml', 'language': 'ru'},
    {'name': 'Inform.kz Politics', 'url': 'https://www.inform.kz/ru/rss/politics', 'language': 'ru'},
    {'name': 'Tengrinews Politics', 'url': 'https://tengrinews.kz/news/kazakhstan_news/politics/feed/', 'language': 'ru'},
    
    # Sport
    {'name': 'Sports.kz', 'url': 'https://www.sports.kz/rss', 'language': 'ru'},
    {'name': 'Vesti.kz', 'url': 'https://vesti.kz/rss/', 'language': 'ru'},
    {'name': 'Prosports.kz', 'url': 'https://prosports.kz/rss', 'language': 'ru'},
    
    # Economy
    {'name': 'Kapital.kz', 'url': 'https://kapital.kz/rss', 'language': 'ru'},
    {'name': 'Forbes.kz', 'url': 'https://forbes.kz/rss', 'language': 'ru'},
    {'name': 'LSM.kz', 'url': 'https://lsm.kz/rss', 'language': 'ru'},
    
    # Tech
    {'name': 'Er10 Tech', 'url': 'https://er10.kz/feed/', 'language': 'ru'},
    {'name': 'Profit.kz', 'url': 'https://profit.kz/rss/', 'language': 'ru'},
    {'name': 'Bluescreen', 'url': 'https://bluescreen.kz/rss/', 'language': 'ru'},
    
    # Auto
    {'name': 'Kolesa.kz', 'url': 'https://kolesa.kz/read/news/feed/', 'language': 'ru'},
    {'name': 'Auto.mail.ru', 'url': 'https://auto.mail.ru/rss/news/', 'language': 'ru'},
    {'name': 'Motor.ru', 'url': 'https://motor.ru/export/rss.xml', 'language': 'ru'},
    
    # World
    {'name': 'Tengrinews World', 'url': 'https://tengrinews.kz/world_news/feed/', 'language': 'ru'},
    {'name': 'Informburo', 'url': 'https://informburo.kz/xml/rss.xml', 'language': 'ru'},
    {'name': 'Vlast.kz', 'url': 'https://vlast.kz/rss.xml', 'language': 'ru'},
    
    # Culture / Society
    {'name': 'The Steppe', 'url': 'https://the-steppe.com/rss', 'language': 'ru'},
    {'name': 'Afisha.ru (Kino)', 'url': 'https://www.afisha.ru/export/rss.xml', 'language': 'ru'},
    {'name': 'Nur.kz (Showbiz)', 'url': 'https://www.nur.kz/rss/showbiz.xml', 'language': 'ru'}
]

app = create_app()
with app.app_context():
    added = 0
    for s in sources:
        existing = Source.query.filter((Source.url == s['url']) | (Source.name == s['name'])).first()
        if not existing:
            new_source = Source(name=s['name'], url=s['url'], language=s['language'], is_active=True)
            db.session.add(new_source)
            added += 1
            print(f"Added {s['name']}")
    db.session.commit()
    print(f"Added {added} new sources.")
