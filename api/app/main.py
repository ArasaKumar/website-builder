from fastapi import FastAPI, File, UploadFile, HTTPException
import os
import cv2
import logging
from typing import Optional

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
UPLOAD_FOLDER = "uploads"
FRAMES_FOLDER = "frames"
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

# Ensure the upload and frames directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)

@app.get("/")
async def root():
    logging.info("Default get api called")
    return {"message": "Running successfully"}

def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def split_video_into_frames(video_path: str, frames_folder: str, num_frames: int) -> None:
    """Split the video into the specified number of frames and save them as images."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise HTTPException(status_code=400, detail="Unable to open the video file.")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, total_frames // num_frames)  # Ensure at least 1 frame is extracted

    for i in range(num_frames):
        frame_id = i * frame_interval
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if not ret:
            break

        frame_filename = os.path.join(frames_folder, f"frame_{i + 1}.jpg")
        cv2.imwrite(frame_filename, frame)
        logging.info(f"Saved frame {i + 1} to {frame_filename}")

    cap.release()

@app.post("/upload-video/")
async def upload_video(file: UploadFile = File(...), num_frames: Optional[int] = 10):
    """API to upload a video file and split it into frames."""
    # Validate file size
    if file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds the 100 MB limit.")

    # Validate file extension
    if not allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="File type not allowed.")

    # Save the uploaded video file
    video_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(video_path, "wb") as buffer:
        buffer.write(await file.read())
    logging.info(f"Video saved to {video_path}")

    # Create a folder for frames
    frames_folder = os.path.join(FRAMES_FOLDER, os.path.splitext(file.filename)[0])
    os.makedirs(frames_folder, exist_ok=True)

    # Split the video into frames
    split_video_into_frames(video_path, frames_folder, num_frames)

    return {"message": f"Video successfully split into {num_frames} frames and saved in {frames_folder}"}