from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, File, HTTPException, UploadFile

import frame_extract


app = FastAPI()

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}


@app.post("/video")
async def upload_video(file: UploadFile = File(...)):
	suffix = Path(file.filename or "").suffix.lower()
	if suffix not in VIDEO_EXTENSIONS:
		raise HTTPException(status_code=400, detail="Unsupported video file type")

	temporary_path = None
	try:
		with NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
			temporary_path = Path(temporary_file.name)
			while chunk := await file.read(1024 * 1024):
				temporary_file.write(chunk)

		frames = frame_extract.extract_frames(str(temporary_path))
		return {"frames": frames}
	except HTTPException:
		raise
	except Exception as exc:
		raise HTTPException(status_code=500, detail="Video processing failed") from exc
	finally:
		await file.close()
		if temporary_path is not None:
			temporary_path.unlink(missing_ok=True)
