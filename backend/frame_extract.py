from pathlib import Path

import cv2

def extract_frames(video_path):
    output_dir = Path("frames")

    output_dir.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    frame_index = 0
    try:
        while True:
            success, frame = capture.read()
            if not success:
                break

            frame_path = output_dir / f"frame_{frame_index:06d}.jpg"
            if not cv2.imwrite(str(frame_path), frame):
                raise RuntimeError(f"Could not save frame: {frame_path}")
            frame_index += 1
    finally:
        capture.release()

    print(f"Extracted {frame_index} frames to {output_dir}")


