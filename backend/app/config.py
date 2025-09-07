import os
from dotenv import load_dotenv

load_dotenv()

class config:
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    
    # These are the labels we want the AI to classify prompts into
    LABELS = [
        "increase brightness", 
        "decrease brightness",
        "increase contrast", 
        "decrease contrast",
        "increase saturation", 
        "decrease saturation",
        "remove background",
        "no change needed"
    ]

    CONFIDENCE_THRESHOLD = 0.3