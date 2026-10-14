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

REGISTERED = {} 
SHA_INDEX = {}  

VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
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

        
        if sha in SHA_INDEX:
            existing_id = SHA_INDEX[sha]
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate video: exact file already registered (ID: {existing_id})"
            )

        
        meta, hashes = await asyncio.to_thread(process, path)

        for existing_id, data in REGISTERED.items():
            result = analyzer.compare(data["meta"], data["hashes"], meta, hashes)
            # If perceptual similarity is high (e.g., >= 95% identical frames)
            if result.get("overall_similarity", 0) >= 95:
                raise HTTPException(
                    status_code=409,
                    detail=f"Duplicate content: video matches existing record {existing_id} ({result['overall_similarity']}% similar)"
                )

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
        path, sha = await save_upload(file)

        # note from diego - i have no idea what any of this means, i dont think it broke anything though

        # Exact-match check. SHA_INDEX maps the SHA-256 of every registered file to its
        # record ID, so this finds the record for an identical file no matter when it was
        # registered. The default lookup below only checks the most recent registration.

        # If this exact file was registered at any point, return that record
        if sha in SHA_INDEX:
            rec_id = SHA_INDEX[sha]
            return {"exact_match": True, "record_id": rec_id, "overall_similarity": 100,
                    "is_authentic": True, "alterations": {}, "frames": []}

        rec_id = record_id or next(reversed(REGISTERED), None)
        if rec_id is None or rec_id not in REGISTERED:
            raise HTTPException(status_code=404, detail="No registered original found")
        rec = REGISTERED[rec_id]

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