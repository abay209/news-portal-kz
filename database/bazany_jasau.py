# bazany_jasau.py — Базаны бірінші рет жасайды (кестелер + admin пайдаланушысы)
# Іске қосу: python database/bazany_jasau.py (proekt/ папкасынан)

import sys
import os

# Жоғарыдағы папканы (proekt/) Python жолына қосу
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, Category

app = create_app()

with app.app_context():
    db.create_all()

    # Категориялар жоқ болса, әдепкі категориялар қосу
    if Category.query.count() == 0:
        categories = [
            'cat_general', 'cat_politics', 'cat_sport',
            'cat_economy', 'cat_tech', 'cat_world',
            'cat_auto', 'cat_culture'
        ]
        for c in categories:
            cat = Category(code=c)
            db.session.add(cat)
        db.session.commit()
        print("Категориялар сәтті қосылды.")

    # Admin пайдаланушысы жоқ болса, жасау
    if User.query.filter_by(username='admin').first() is None:
        admin_user = User(username='admin')
        admin_user.set_password('admin')
        db.session.add(admin_user)
        db.session.commit()
        print("'admin' пайдаланушысы 'admin' паролімен жасалды.")

    print("База данных сәтті инициализацияланды.")
