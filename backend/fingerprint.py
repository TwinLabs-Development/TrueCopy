import re
from pathlib import Path
import cv2
import imagehash
from PIL import Image

GRID_ROWS = 3
GRID_COLS = 3
TILE_HASH_SIZE = 8

BASE_DIR = Path(__file__).resolve().parent


def get_meta(video_path: str):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {"width": 0, "height": 0, "fps": 0.0, "frame_count": 0, "duration_ms": 0.0}

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_ms = (frame_count / fps * 1000.0) if fps > 0 else 0.0

    cap.release()
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count,
        "duration_ms": duration_ms,
    }


def _resolve_image_path(raw_path: str) -> Path | None:
    if not raw_path:
        return None
    clean = raw_path.lstrip("/\\").replace("\\", "/")
    candidates = [
        Path(clean),
        BASE_DIR / clean,
        BASE_DIR.parent / clean,
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return None


def compute_frame_fingerprint(image_input):
    """Computes global pHash + 3x3 dHash tiles."""
    cv_img = None
    if isinstance(image_input, (str, Path)):
        resolved = _resolve_image_path(str(image_input))
        if resolved:
            cv_img = cv2.imread(str(resolved))
    else:
        cv_img = image_input

    if cv_img is None or cv_img.size == 0:
        return None

    h, w = cv_img.shape[:2]
    if h < GRID_ROWS or w < GRID_COLS:
        return None

    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    pil_img = Image.fromarray(gray)

    global_hash = imagehash.phash(pil_img, hash_size=8)

    tile_hashes = []
    tile_h, tile_w = h // GRID_ROWS, w // GRID_COLS

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            y1, y2 = r * tile_h, (r + 1) * tile_h
            x1, x2 = c * tile_w, (c + 1) * tile_w
            tile_pil = Image.fromarray(gray[y1:y2, x1:x2])
            tile_hashes.append(imagehash.dhash(tile_pil, hash_size=TILE_HASH_SIZE))

    return {
        "global_hash": global_hash,
        "tile_hashes": tile_hashes,
    }


def hash_frames(extracted_frame_urls):
    fingerprints = []
    for item in extracted_frame_urls:
        url = item.get("url") if isinstance(item, dict) else str(item)

        # Resilient timestamp extraction: dict -> filename regex -> 0.0
        if isinstance(item, dict) and "t_ms" in item:
            t_ms = float(item["t_ms"])
        else:
            match = re.search(r"_(\d+)ms", url)
            t_ms = float(match.group(1)) if match else 0.0

        fp = compute_frame_fingerprint(url)
        if fp:
            fingerprints.append({
                "t_ms": t_ms,
                "url": url,
                "hash": fp["global_hash"],
                "tile_hashes": fp["tile_hashes"],
            })
    return fingerprints