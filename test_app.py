import os
import sys

# Add project dir to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from app import create_app
    app = create_app()
    with app.app_context():
        client = app.test_client()
        response = client.get('/')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
            print("Response Data:")
            print(response.data.decode('utf-8'))
except Exception as e:
    import traceback
    traceback.print_exc()
