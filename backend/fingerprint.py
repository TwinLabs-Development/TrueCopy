import re
from pathlib import Path

import cv2
import imagehash
from PIL import Image


def hash_frames(frame_urls: list[str]) -> list[dict]:
    out = []
    for url in frame_urls:
        path = Path("static") / url.removeprefix("/static/")
        t_ms = int(re.search(r"_(\d+)ms\.jpg$", url).group(1))
        with Image.open(path) as img:
            out.append({"t_ms": t_ms, "hash": imagehash.phash(img), "url": url})
    return out


def get_meta(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    meta = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": round(fps, 2),
        "duration_ms": int(total / fps * 1000) if fps else 0,
    }
    cap.release()
    return meta