import requests
from .config import config

def test_huggingface_api():
    """Test the Hugging Face API """

    headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}

    payload = {
        "inputs": "make the image brighter",
        "parameters": {"candidate_labels": config.LABELS},
        "options": {"wait for model": True}
    }

    try:
        response = requests.post(config.API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            print("API connection successful!")
            result = response.json()
            print(f"API response: {result}")
            return True
        elif response.status_code == 403:
            print("API token is invalid or doesn't have correct permissions")
            print("Make sure you created a READ token, not a WRITE token")
            return False
        elif response.status_code == 503:
            print("Model is loading, please try again in a few seconds")
            return False
        else:
            print(f"Unexpected error: {response.status_code} - {response.text}")
            return False
    
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_huggingface_api()
