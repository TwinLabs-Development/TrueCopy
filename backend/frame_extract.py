import uuid
from pathlib import Path
import cv2

samplesTaken = 2

# Base directory for all extracted outputs
FRAMES_BASE_DIR = Path("static/frames")

def extract_frames(video_path: str, fps_sample: float = samplesTaken) -> list[str]:
    """
    Extracts frames at a target sampling rate based on millisecond timestamps.
    Handles variable frame rates and differing FPS formats consistently.
    """
    session_id = uuid.uuid4().hex
    output_dir = FRAMES_BASE_DIR / session_id
    output_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    # Interval in milliseconds (e.g., 2 samples/sec = every 500 ms)
    interval_ms = 1000.0 / fps_sample
    next_capture_ms = 0.0

    frame_index = 0
    saved_paths = []

    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            current_msec = capture.get(cv2.CAP_PROP_POS_MSEC)

            # Sample when the playback position hits or crosses the target millisecond mark
            if current_msec >= next_capture_ms:
                filename = f"frame_{frame_index:06d}_{int(current_msec)}ms.jpg"
                frame_path = output_dir / filename

                if cv2.imwrite(str(frame_path), frame, [cv2.IMWRITE_JPEG_QUALITY, 80]):
                    saved_paths.append(f"/static/frames/{session_id}/{filename}")
                    frame_index += 1

                # Schedule the next timestamp target
                next_capture_ms += interval_ms
    finally:
        capture.release()

    return saved_paths