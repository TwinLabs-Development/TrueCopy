from pathlib import Path
from tempfile import NamedTemporaryFile
import traceback
import asyncio
import hashlib
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import analyzer
import fingerprint
import frame_extract

REGISTERED = {}  # record_id -> {sha256, meta, hashes}
SHA_INDEX = {}   # sha256 -> record_id

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def save_upload(file: UploadFile):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported video file type")
    sha = hashlib.sha256()
    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        path = Path(tmp.name)
        while chunk := await file.read(1024 * 1024):
            tmp.write(chunk)
            sha.update(chunk)
    return path, sha.hexdigest()


def process(path: Path):
    meta = fingerprint.get_meta(str(path))
    urls = frame_extract.extract_frames(str(path))
    return meta, fingerprint.hash_frames(urls)


@app.post("/register")
async def register(file: UploadFile = File(...)):
    path = None
    try:
        path, sha = await save_upload(file)

        # Check if already registered
        if sha in SHA_INDEX:
            existing_id = SHA_INDEX[sha]
            raise HTTPException(
                status_code=409,  # 409 Conflict
                detail=f"This video is already registered (Record ID: {existing_id})"
            )

        meta, hashes = await asyncio.to_thread(process, path)
        record_id = uuid.uuid4().hex[:8]
        REGISTERED[record_id] = {"sha256": sha, "meta": meta, "hashes": hashes}
        SHA_INDEX[sha] = record_id

        return {
            "status": "Registered successfully",
            "record_id": record_id,
            "sha256": sha,
            "metadata": meta,
            "total_frames_sampled": len(hashes),
        }
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Registration failed") from exc
    finally:
        await file.close()
        if path is not None:
            path.unlink(missing_ok=True)

@app.post("/verify")
async def verify(file: UploadFile = File(...), record_id: str | None = None):
    path = None
    try:
        rec_id = record_id or next(reversed(REGISTERED), None)
        if rec_id is None or rec_id not in REGISTERED:
            raise HTTPException(status_code=404, detail="No registered original found")
        rec = REGISTERED[rec_id]

        path, sha = await save_upload(file)

        # Check 1: exact byte-for-byte match
        if sha == rec["sha256"]:
            return {"exact_match": True, "record_id": rec_id, "overall_similarity": 100,
                    "is_authentic": True, "alterations": {}, "frames": []}

        # Check 2: perceptual comparison
        meta, hashes = await asyncio.to_thread(process, path)
        result = analyzer.compare(rec["meta"], rec["hashes"], meta, hashes)
        return {"exact_match": False, "record_id": rec_id, **result}
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Verification failed") from exc
    finally:
        await file.close()
        if path is not None:
            path.unlink(missing_ok=True)