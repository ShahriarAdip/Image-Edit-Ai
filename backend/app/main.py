from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageEnhance
import os
import uuid
from typing import Annotated
from pydantic import BaseModel
from .ai_processor import AiProcessor
from .background_removal import remove_background

app_version = "1.0.0"
app = FastAPI(title="ImageEdit Ai", version=app_version)

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

# Pydantic model for form data
# class ImageAdjustments(BaseModel):
#     brightness: float = 1.0
#     contrast: float = 1.0
#     saturation: float = 1.0



@app.get("/")
def read_root():
    return {"Message": "Welcome to ImageEdit Ai"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "service": "ImageEdit Ai",
        "version": app_version,
    }


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    # Check valid file extension
    file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    accepted_extensions = ["jpg", "jpeg", "png", "bmp", "gif"]

    if file_extension.lower() not in accepted_extensions:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    try:
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"uploads/{filename}"

        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {"filename": filename, "message": "File uploaded successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process/")
async def process_image(
    file: UploadFile = File(...),
    brightness: Annotated[float, Form()] = 1.0,
    contrast: Annotated[float, Form()] = 1.0,
    saturation: Annotated[float, Form()] = 1.0
):
    try:
        # Check file extension
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        accepted_extensions = ["jpg", "jpeg", "png", "bmp", "gif"]
        
        if file_extension.lower() not in accepted_extensions:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        input_filename = f"{uuid.uuid4()}.{file_extension}"
        output_filename = f"{uuid.uuid4()}_processed.{file_extension}"

        input_path = f"uploads/{input_filename}"
        output_path = f"processed/{output_filename}"

        # Save uploaded file
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Open image and apply transformations
        image = Image.open(input_path)

        # Adjust brightness
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)

        # Adjust contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)

        # Adjust saturation
        if saturation != 1.0:
            enhancer = ImageEnhance.Color(image)
            image = enhancer.enhance(saturation)

        # Save processed image
        image.save(output_path)

        return {
            "message": "Image processed successfully",
            "processed_url": f"/download/{output_filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    

@app.post("/ai_process/")
async def ai_process_image(
    file: UploadFile = File(...),
    prompt: str = Form(...)
):
    try:
        # Use AI to understand what the user wants
        action = ai_processor.classify_prompt(prompt)
        print(f"Ai prompt '{prompt}' and found {len(action)} actions")

        # create unique filenames
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        input_filename = f"{uuid.uuid4()}.{file_extension}"
        output_filename = f"{uuid.uuid4()}_processed.{file_extension}"

        input_path = f"uploads/{input_filename}"
        output_path = f"processed/{output_filename}"

        # save uploaded file
        with open(input_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # open image
        image = Image.open(input_path)

        # Apply actions
        adjustment_applied = {}
        background_removed = False  # Initialize the variable here

        for act in action:
            action_name = act["action"]
            action_confidence = act["confidence"]

            if action_name == "increase brightness":
                adjust_amount = 1 + action_confidence  # Scale by confidence
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(adjust_amount)  
                adjustment_applied["brightness"] = adjust_amount

            elif action_name == "decrease brightness":
                adjust_amount = max(0, 1 - action_confidence)
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(adjust_amount)
                adjustment_applied["brightness"] = adjust_amount

            elif action_name == "increase contrast":
                adjust_amount = 1 + action_confidence
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(adjust_amount)
                adjustment_applied["contrast"] = adjust_amount

            elif action_name == "decrease contrast":
                adjust_amount = max(0, 1 - action_confidence)
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(adjust_amount)
                adjustment_applied["contrast"] = adjust_amount

            elif action_name == "increase saturation":
                adjust_amount = 1 + action_confidence
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(adjust_amount)
                adjustment_applied["saturation"] = adjust_amount

            elif action_name == "decrease saturation":
                adjust_amount = max(0, 1 - action_confidence)
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(adjust_amount)
                adjustment_applied["saturation"] = adjust_amount

            elif action_name == "remove background":
                image = remove_background(image)
                adjustment_applied["background_removal"] = True
                background_removed = True
        
        # Save processed image
        if background_removed:
            image.save(output_path, format="PNG")  # Save as PNG to preserve transparency
        else:
            image.save(output_path)
        
        return {
            "message": "Image processed successfully",
            "processed_url": f"/download/{output_filename}",
            "ai_actions": action,
            "adjustments_applied": adjustment_applied
        }
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