from pathlib import Path
from tempfile import NamedTemporaryFile
import traceback
import asyncio
import hashlib
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import analyzer
import fingerprint
import frame_extract

REGISTERED = {}  # record_id -> {sha256, meta, hashes}
SHA_INDEX = {}   # sha256 -> record_id

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
        raise HTTPException(status_code=400, detail=f"Unsupported format: '{suffix}'")

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
    hashes = fingerprint.hash_frames(urls)
    return meta, hashes


@app.post("/register")
async def register(file: UploadFile = File(...)):
    path = None
    try:
        path, sha = await save_upload(file)

        # 1. Exact byte duplicate rejection
        if sha in SHA_INDEX:
            existing_id = SHA_INDEX[sha]
            raise HTTPException(
                status_code=409,
                detail=f"Video already registered with Record ID: {existing_id}",
            )

        meta, hashes = await asyncio.to_thread(process, path)

        if not hashes:
            raise HTTPException(status_code=422, detail="Failed to extract readable frames from video.")

        # 2. Perceptual duplicate check
        for rec_id, rec in REGISTERED.items():
            result = analyzer.compare(rec["meta"], rec["hashes"], meta, hashes)
            if result.get("overall_similarity", 0) >= 99.0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Perceptual duplicate of registered record '{rec_id}' ({result['overall_similarity']}% similarity).",
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
        raise HTTPException(status_code=500, detail="Internal registration failure.") from exc
    finally:
        await file.close()
        if path is not None:
            path.unlink(missing_ok=True)


@app.post("/verify")
async def verify(file: UploadFile = File(...), record_id: str | None = None):
    path = None
    try:
        if not REGISTERED:
            raise HTTPException(status_code=404, detail="No registered baseline videos found.")

        path, sha = await save_upload(file)

        # 1. Fast byte-level exact check
        if sha in SHA_INDEX:
            matched_id = SHA_INDEX[sha]
            return {
                "exact_match": True,
                "record_id": matched_id,
                "verdict": "authentic",
                "overall_similarity": 100.0,
                "is_authentic": True,
                "alterations": {
                    "visually_altered": {"detected": False, "segments": [], "flagged_timestamps": [], "details": "Byte-identical."},
                    "time_altered": {"detected": False, "details": "Byte-identical."},
                    "quality_altered": {"detected": False, "details": "Byte-identical."},
                    "audio_altered": {"detected": False, "details": "Byte-identical."},
                },
                "frames": [],
                "message": "Exact byte-for-byte duplicate of registered master.",
            }

        # 2. Select matching scope
        if record_id:
            if record_id not in REGISTERED:
                raise HTTPException(status_code=404, detail=f"Record ID '{record_id}' not found.")
            target_records = {record_id: REGISTERED[record_id]}
        else:
            target_records = REGISTERED

        # 3. Extract & compare
        meta, hashes = await asyncio.to_thread(process, path)
        if not hashes:
            raise HTTPException(status_code=422, detail="Failed to sample video frames.")

        best_match_id = None
        best_result = None
        highest_similarity = -1.0

        for r_id, rec in target_records.items():
            result = analyzer.compare(rec["meta"], rec["hashes"], meta, hashes)
            sim = result.get("overall_similarity", 0.0)
            if sim > highest_similarity:
                highest_similarity = sim
                best_match_id = r_id
                best_result = result

        return {
            "exact_match": False,
            "record_id": best_match_id,
            **best_result,
        }
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Verification analysis failed.") from exc
    finally:
        await file.close()
        if path is not None:
            path.unlink(missing_ok=True)