import requests
import json
import sys

def check_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "codellama",
        "prompt": "Write a one-line comment in TypeScript saying 'Hello Playwright'.",
        "stream": False
    }
    
    print(f"Testing connection to {url} with model 'codellama'...")
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print("\n✅ Success! Ollama Responded:")
        print(f"Response: {data.get('response', '').strip()}")
        return True
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Ollama. Is it running on port 11434?")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e}")
        print(f"Response Body: {response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = check_ollama()
    if not success:
        sys.exit(1)
