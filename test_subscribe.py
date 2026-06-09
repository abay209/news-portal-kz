import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
app = create_app()

with app.app_context():
    client = app.test_client()
    response = client.post('/subscribe', data={'email': 'test@example.com'})
    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        print("Response Data:")
        print(response.data.decode('utf-8'))
