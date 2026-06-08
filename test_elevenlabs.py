import requests

api_key = "sk_7ef9cb644d47d3d09ba9c7c99258cc4da56e6a272f9f5ab7"
voice_id = "21m00Tcm4TlvDq8ikWAM" # Rachel
url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": api_key
}

data = {
    "text": "Сәлем, бұл сынақ дауысы.",
    "model_id": "eleven_multilingual_v2",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
    }
}

response = requests.post(url, json=data, headers=headers)
if response.status_code == 200:
    print("Success: audio generated")
else:
    print(f"Error: {response.status_code} - {response.text}")
