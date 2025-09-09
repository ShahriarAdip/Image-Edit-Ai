# /backend/app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageEnhance  # Add this import
import os
import uuid
from typing import Annotated

from .models import (
    HealthCheckResponse, UploadResponse, ProcessRequest, 
    AIProcessRequest, ProcessResponse
)
from .services.image_service import ImageService
from .services.ai_processor import AiProcessor
from .config import config

app_version = "1.0.1"
app = FastAPI(title="ImageEdit AI", version=app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for uploads if they don't exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("processed", exist_ok=True)

# Initialize AI processor
ai_processor = AiProcessor()

@app.get("/")
async def read_root():
    return {"Message": "Welcome to ImageEdit AI"}

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    return HealthCheckResponse(
        status="healthy", 
        service="ImageEdit AI",
        version=app_version,
    )

@app.post("/upload/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    # Check valid file extension
    if not ImageService.validate_extension(file.filename):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    try:
        filename = ImageService.generate_filename(file.filename)
        file_path = f"uploads/{filename}"

        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return UploadResponse(filename=filename, message="File uploaded successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/", response_model=ProcessResponse)
async def process_image(
    file: UploadFile = File(...),
    adjustments: ProcessRequest = Depends()
):
    try:
        if not ImageService.validate_extension(file.filename):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        input_filename = ImageService.generate_filename(file.filename)
        output_filename = ImageService.generate_filename(file.filename, "_processed")

        input_path = f"uploads/{input_filename}"
        output_path = f"processed/{output_filename}"

        # Save uploaded file
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Open image and apply transformations
        image = Image.open(input_path)
        image = ImageService.apply_adjustments(
            image,
            brightness=adjustments.brightness,
            contrast=adjustments.contrast,
            saturation=adjustments.saturation
        )

        # Save processed image
        image.save(output_path)

        return ProcessResponse(
            message="Image processed successfully",
            processed_url=f"/download/{output_filename}"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.post("/ai_process/", response_model=ProcessResponse)
async def ai_process_image(
    file: UploadFile = File(...),
    ai_request: AIProcessRequest = Depends()
):
    try:
        if not ImageService.validate_extension(file.filename):
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Use AI to understand what the user wants
        actions = ai_processor.classify_prompt(ai_request.prompt)
        print(f"AI prompt '{ai_request.prompt}' found {len(actions)} actions")

        # Generate filenames
        input_filename = ImageService.generate_filename(file.filename)
        output_filename = ImageService.generate_filename(file.filename, "_processed")

        input_path = f"uploads/{input_filename}"
        output_path = f"processed/{output_filename}"

        # Save uploaded file
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Open image
        image = Image.open(input_path)
        adjustment_applied = {}
        background_removed = False

        # Apply AI-suggested actions
        if actions:
            for act in actions:
                if act.action == "increase brightness":
                    adjust_amount = 1 + act.confidence
                    enhancer = ImageEnhance.Brightness(image)
                    image = enhancer.enhance(adjust_amount)  
                    adjustment_applied["brightness"] = adjust_amount

                elif act.action == "decrease brightness":
                    adjust_amount = max(0.1, 1 - act.confidence)
                    enhancer = ImageEnhance.Brightness(image)
                    image = enhancer.enhance(adjust_amount)
                    adjustment_applied["brightness"] = adjust_amount

                elif act.action == "increase contrast":
                    adjust_amount = 1 + act.confidence
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(adjust_amount)
                    adjustment_applied["contrast"] = adjust_amount

                elif act.action == "decrease contrast":
                    adjust_amount = max(0.1, 1 - act.confidence)
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(adjust_amount)
                    adjustment_applied["contrast"] = adjust_amount

                elif act.action == "increase saturation":
                    adjust_amount = 1 + act.confidence
                    enhancer = ImageEnhance.Color(image)
                    image = enhancer.enhance(adjust_amount)
                    adjustment_applied["saturation"] = adjust_amount

                elif act.action == "decrease saturation":
                    adjust_amount = max(0.1, 1 - act.confidence)
                    enhancer = ImageEnhance.Color(image)
                    image = enhancer.enhance(adjust_amount)
                    adjustment_applied["saturation"] = adjust_amount

                elif act.action == "remove background":
                    image = ImageService.remove_background(image)
                    adjustment_applied["background_removal"] = True
                    background_removed = True
        
        # Save processed image
        if background_removed:
            image.save(output_path, format="PNG")
        else:
            image.save(output_path)
        
        return ProcessResponse(
            message="Image processed successfully",
            processed_url=f"/download/{output_filename}",
            ai_actions=actions,
            adjustments_applied=adjustment_applied
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    # Security check to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = f"processed/{filename}"

    if os.path.exists(file_path):
        extension = filename.split(".")[-1].lower()
        media_type = f"image/{extension}"
        return FileResponse(file_path, media_type=media_type, filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)