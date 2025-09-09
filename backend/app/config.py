# /backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
    
    LABELS = [
        "increase brightness", "decrease brightness",
        "increase contrast", "decrease contrast",
        "increase saturation", "decrease saturation",
        "remove background", "no change needed"
    ]
    
    CONFIDENCE_THRESHOLD = 0.3
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "gif"}
    MAX_FILE_SIZE_MB = 10
    API_TIMEOUT_SECONDS = 30

config = Config()