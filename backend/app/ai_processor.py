import requests
import time
from .config import config

class AiProcessor:
    def __init__(self):
        self.api_key = config.HUGGINGFACE_API_KEY
        self.api_url = config.API_URL
        self.api_labels = config.LABELS
        self.headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}
        self.confidence_threshold = config.CONFIDENCE_THRESHOLD


    def classify_prompt(self, prompt: str, max_retries: int = 3):
        """
        Use AI to classify what image edits the user wants
        Returns a list of actions with their confidence scores
        """
        payload = {
            "inputs": prompt,
            "parameters": {"candidate_labels": self.api_labels},
            "options": {"wait_for_model": True}
        }

        # Try multiple times in case the model is loading
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=10)
            
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if we got a valid response
                    if "labels" in result and "scores" in result:
                        actions = []

                        for label, score in zip(result["labels"], result["scores"]):
                            if score >= self.confidence_threshold and label != "no change needed":
                                actions.append({"action": label, "confidence": score})

                        # Sort by confidence (highest first)
                        actions.sort(key=lambda x: x["confidence"], reverse=True)

                        print(f"Ai classified prompt '{prompt}', found {len(actions)} actions.")
                        for action in actions:
                            print(f" - {action['action']} (confidence: {action['confidence']:.2f})")

                    
                        return actions
                    else:
                        print(f"Unexpected API response format: {result}")
                    
                

                elif response.status_code == 503:
                    # Model is loading, wait and try again
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Model is loading, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                    
                elif response.status_code == 403:
                    print("API token error - check your token permissions")
                    
                else:
                    print(f"API error {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                print("API request timed out")                
                
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}")                
        
        print("All retries failed")
        


