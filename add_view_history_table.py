from app import create_app, db
from app.models import ViewHistory

app = create_app()

with app.app_context():
    # Only create the missing tables
    db.create_all()
    print("Database tables created/updated successfully.")
