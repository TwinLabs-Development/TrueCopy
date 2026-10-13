from pathlib import Path
from tempfile import NamedTemporaryFile
import traceback

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import frame_extract

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure the static folder exists and allow web access to saved frames
Path("static/frames").mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}


@app.post("/video")
async def upload_video(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported video file type")

    temporary_path = None
    try:
        # Step 1: Write and fully CLOSE the file handle so Windows releases the lock
        with NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            temporary_path = Path(temporary_file.name)
            while chunk := await file.read(1024 * 1024):
                temporary_file.write(chunk)
            temporary_file.flush()

        # Step 2: Now OpenCV can safely read the video path without permission errors
        print(f"Processing video: {temporary_path}")
        frames = frame_extract.extract_frames(str(temporary_path))
        print(f"Extracted {len(frames)} frames successfully.")

        return {"frames": frames}

    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Video processing failed") from exc
    finally:
        await file.close()
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
