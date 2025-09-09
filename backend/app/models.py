# /backend/app/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class HealthCheckResponse(BaseModel):
    status: str
    service: str
    version: str

class UploadResponse(BaseModel):
    filename: str
    message: str

class ProcessRequest(BaseModel):
    brightness: float = Field(1.0, ge=0.0, le=3.0, description="Brightness factor (0.0 - 3.0)")
    contrast: float = Field(1.0, ge=0.0, le=3.0, description="Contrast factor (0.0 - 3.0)")
    saturation: float = Field(1.0, ge=0.0, le=3.0, description="Saturation factor (0.0 - 3.0)")

class AIProcessRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User prompt for image editing")

class AIAction(BaseModel):
    action: str
    confidence: float

class ProcessResponse(BaseModel):
    message: str
    processed_url: str
    ai_actions: Optional[List[AIAction]] = None
    adjustments_applied: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    detail: str