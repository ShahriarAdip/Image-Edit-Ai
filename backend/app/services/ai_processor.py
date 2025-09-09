# /backend/app/services/ai_processor.py
import requests
import time
from typing import List, Optional
from ..config import config
from ..models import AIAction

class AiProcessor:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}

    def classify_prompt(self, prompt: str, max_retries: int = 3) -> List[AIAction]:
        """
        Use AI to classify what image edits the user wants
        Returns a list of actions with their confidence scores
        """
        payload = {
            "inputs": prompt,
            "parameters": {"candidate_labels": config.LABELS},
            "options": {"wait_for_model": True}
        }

        # Try multiple times in case the model is loading
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    config.API_URL, 
                    headers=self.headers, 
                    json=payload, 
                    timeout=10
                )
            
                if response.status_code == 200:
                    result = response.json()
                    return self._parse_response(result)
                
                elif response.status_code == 503:
                    # Model is loading, wait and try again
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Model is loading, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                    
                else:
                    print(f"API error {response.status_code}: {response.text}")
                    break
                    
            except requests.exceptions.Timeout:
                print("API request timed out")
                if attempt == max_retries - 1:
                    raise TimeoutError("AI classification timed out")
                    
            except requests.exceptions.RequestException as e:
                print(f"Network error: {e}")
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to AI service: {str(e)}")

        return []

    def _parse_response(self, result: dict) -> List[AIAction]:
        """
        Parse the API response and convert to AIAction objects
        """
        actions = []
        
        if "labels" in result and "scores" in result:
            for label, score in zip(result["labels"], result["scores"]):
                # Skip low confidence results and "no change needed"
                if score >= config.CONFIDENCE_THRESHOLD and label != "no change needed":
                    actions.append(AIAction(action=label, confidence=score))
            
            # Sort by confidence (highest first)
            actions.sort(key=lambda x: x.confidence, reverse=True)
            
            print(f"Found {len(actions)} actions:")
            for action in actions:
                print(f" - {action.action} (confidence: {action.confidence:.2f})")
        
        return actions