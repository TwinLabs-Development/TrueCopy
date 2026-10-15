import re
import shutil
import subprocess
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

try:
    import imagehash
except ImportError:
    imagehash = None

GRID_ROWS = 3
GRID_COLS = 3
TILE_HASH_SIZE = 8

AUDIO_SR = 8000
# 8 log-spaced frequency bands across a 512-point real FFT (at 8 kHz sample rate)
AUDIO_BAND_EDGES = (1, 3, 7, 14, 26, 46, 76, 112, 160)

BASE_DIR = Path(__file__).resolve().parent

# Cache the most recently decoded audio stream so hash_frames(urls) works
# even when called without passing video_path explicitly.
_LAST_AUDIO_CACHE: dict[str, np.ndarray | None] = {"path": None, "pcm": None}


class _FallbackHash:
    """Lightweight fallback matching imagehash.ImageHash subtraction semantics."""

    def __init__(self, bits: np.ndarray):
        self.hash = bits.astype(bool)

    def __sub__(self, other: "_FallbackHash") -> int:
        return int(np.count_nonzero(self.hash != other.hash))


def _phash(pil_img: Image.Image, hash_size: int = 8):
    if imagehash is not None:
        return imagehash.phash(pil_img, hash_size=hash_size)
    resized = np.asarray(pil_img.resize((hash_size * 4, hash_size * 4), Image.Resampling.LANCZOS), dtype=np.float32)
    dct = cv2.dct(resized)[:hash_size, :hash_size]
    med = np.median(dct.flatten()[1:])
    return _FallbackHash(dct > med)


def _dhash(pil_img: Image.Image, hash_size: int = 8):
    if imagehash is not None:
        return imagehash.dhash(pil_img, hash_size=hash_size)
    resized = np.asarray(pil_img.resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS), dtype=np.float32)
    return _FallbackHash(resized[:, 1:] > resized[:, :-1])


def _resolve_ffmpeg() -> str | None:
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        return ffmpeg_bin
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def extract_audio_pcm(video_path: str, sr: int = AUDIO_SR) -> np.ndarray | None:
    """Decodes the video's primary audio stream to mono float32 PCM in [-1, 1]."""
    ffmpeg_bin = _resolve_ffmpeg()
    if not ffmpeg_bin:
        return None

    try:
        proc = subprocess.run(
            [
                ffmpeg_bin,
                "-v", "error",
                "-i", str(video_path),
                "-vn",
                "-ac", "1",
                "-ar", str(sr),
                "-f", "s16le",
                "-",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0 or not proc.stdout:
            return None
        pcm = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        return pcm if pcm.size > 0 else None
    except Exception:
        return None


def _subframe_bits(band_energies: np.ndarray) -> np.ndarray:
    """
    Computes a 64-bit audio hash from a (9, 8) time-frequency log-energy matrix:
    - 32 temporal derivative bits (8 time transitions x 4 paired frequency bands)
    - 32 spectral profile bits (4 pooled time blocks x 8 bands relative to block median)
    """
    paired_bands = band_energies.reshape(9, 4, 2).mean(axis=2)
    temporal_bits = (paired_bands[1:, :] > paired_bands[:-1, :]).astype(np.uint8).flatten()

    pooled_time = band_energies[:8, :].reshape(4, 2, 8).mean(axis=1)
    medians = np.median(pooled_time, axis=1, keepdims=True)
    spectral_bits = (pooled_time > medians).astype(np.uint8).flatten()

    return np.concatenate([temporal_bits, spectral_bits])


def compute_audio_window_hash(pcm: np.ndarray | None, t_ms: float, sr: int = AUDIO_SR) -> dict:
    """
    Computes a 64-bit temporal-spectral perceptual hash at timestamp t_ms,
    including +/-80ms sub-frame phase shifts so off-grid video trims align cleanly.
    """
    if pcm is None or pcm.size == 0:
        return {"has_audio": False, "silent": True, "rms": 0.0, "bits": None, "shifted_bits": None}

    sub_len = int(0.04 * sr)  # 40ms per sub-frame (320 samples at 8 kHz)
    n_total_sub = 13          # 520ms window covering 5 overlapping 9-sub-frame (360ms) slices
    total_len = n_total_sub * sub_len
    start = int(round(((t_ms - 80.0) / 1000.0) * sr))

    if start < 0:
        pad_left = -start
        seg = pcm[0 : max(0, total_len - pad_left)]
        seg = np.pad(seg, (pad_left, max(0, total_len - pad_left - seg.size)))
    else:
        seg = pcm[start : start + total_len]
        if seg.size < total_len:
            seg = np.pad(seg, (0, total_len - seg.size))

    center_seg = seg[2 * sub_len : 11 * sub_len]
    rms = float(np.sqrt(np.mean(center_seg ** 2)))
    if rms < 1e-4:
        zero_bits = np.zeros(64, dtype=np.uint8)
        return {
            "has_audio": True,
            "silent": True,
            "rms": rms,
            "bits": zero_bits,
            "shifted_bits": [zero_bits],
        }

    n_bands = len(AUDIO_BAND_EDGES) - 1
    band_energies = np.zeros((n_total_sub, n_bands), dtype=np.float32)

    for t_idx in range(n_total_sub):
        sub = seg[t_idx * sub_len : (t_idx + 1) * sub_len]
        windowed = sub * np.hanning(sub.size)
        spec = np.abs(np.fft.rfft(windowed, n=512))
        for b_idx in range(n_bands):
            lo, hi = AUDIO_BAND_EDGES[b_idx], AUDIO_BAND_EDGES[b_idx + 1]
            band_energies[t_idx, b_idx] = np.log1p(np.mean(spec[lo:hi] ** 2) * 1e4)

    shifted_bits = [_subframe_bits(band_energies[offset : offset + 9]) for offset in range(5)]
    return {
        "has_audio": True,
        "silent": False,
        "rms": rms,
        "bits": shifted_bits[2],
        "shifted_bits": shifted_bits,
    }


def get_meta(video_path: str):
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return {
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "frame_count": 0,
            "duration_ms": 0.0,
            "has_audio": False,
        }

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_ms = (frame_count / fps * 1000.0) if fps > 0 else 0.0

    cap.release()

    pcm = extract_audio_pcm(str(video_path))
    _LAST_AUDIO_CACHE["path"] = str(video_path)
    _LAST_AUDIO_CACHE["pcm"] = pcm
    has_audio = bool(pcm is not None and pcm.size > 0 and float(np.sqrt(np.mean(pcm ** 2))) >= 1e-4)

    return {
        "width": width,
        "height": height,
        "fps": fps,
        "frame_count": frame_count,
        "duration_ms": duration_ms,
        "has_audio": has_audio,
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

    global_hash = _phash(pil_img, hash_size=8)

    tile_hashes = []
    tile_h, tile_w = h // GRID_ROWS, w // GRID_COLS

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            y1, y2 = r * tile_h, (r + 1) * tile_h
            x1, x2 = c * tile_w, (c + 1) * tile_w
            tile_pil = Image.fromarray(gray[y1:y2, x1:x2])
            tile_hashes.append(_dhash(tile_pil, hash_size=TILE_HASH_SIZE))

    return {
        "global_hash": global_hash,
        "tile_hashes": tile_hashes,
    }


def hash_frames(extracted_frame_urls, video_path: str | None = None):
    if video_path is not None:
        if _LAST_AUDIO_CACHE.get("path") == str(video_path):
            pcm = _LAST_AUDIO_CACHE.get("pcm")
        else:
            pcm = extract_audio_pcm(str(video_path))
    else:
        pcm = _LAST_AUDIO_CACHE.get("pcm")

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
                "audio_fp": compute_audio_window_hash(pcm, t_ms),
            })
    return fingerprints