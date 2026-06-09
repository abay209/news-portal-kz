import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
app = create_app()

with app.app_context():
    client = app.test_client()
    routes_to_test = ['/', '/api/search?q=test', '/api/news/latest?since=2023-01-01T00:00:00']
    for r in routes_to_test:
        response = client.get(r)
        print(f"Route {r} - Status Code: {response.status_code}")
        if response.status_code == 500:
            print(f"Error on {r}:")
            print(response.data.decode('utf-8'))
