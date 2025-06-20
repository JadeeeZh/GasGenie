import requests
import json

def test_fireworks():
    # Use API key directly from .env file
    api_key = "fw_3ZaMvVG31Trzt6x3H89ASpES"
    print(f"API Key exists: {bool(api_key)}")
    if api_key:
        print(f"API Key format: {api_key[:3]}...{api_key[-4:]}")
        print(f"API Key length: {len(api_key)}")
        print(f"API Key starts with 'fw_': {api_key.startswith('fw_')}")
    
    url = "https://api.fireworks.ai/inference/v1/chat/completions"
    
    payload = {
        "model": "accounts/fireworks/models/deepseek-v3",
        "max_tokens": 16384,
        "top_p": 1,
        "top_k": 40,
        "presence_penalty": 0,
        "frequency_penalty": 0,
        "temperature": 0.6,
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ]
    }
    
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        print(f"Status code: {response.status_code}")
        print("Response:", response.text)
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    test_fireworks() 