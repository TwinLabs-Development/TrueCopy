# TrueCopy
<img src="https://raw.githubusercontent.com/TwinLabs-Development/TrueCopy/refs/heads/main/TrueCopy.svg" width="350"></img>

[![Last Commit](https://img.shields.io/github/last-commit/TwinLabs-Development/TrueCopy/main)](https://github.com/TwinLabs-Development/TrueCopy/commits/main)
[![GPLv3 License](https://img.shields.io/badge/License-GPL%20v3-yellow.svg)](https://opensource.org/licenses/)

TrueCopy is a tool that checks if a video or its audio has been edited, trimmed, or tampered with. 

You upload an original video to save it into the system, and later you can upload any copy of that video to see if it is still authentic or if someone changed it.

---

## What It Checks For

When you verify a video, TrueCopy compares it against your registered originals and checks four main things:

* **Visual Changes**: Detects if something was added or changed on screen, like watermarks, blurred areas, text overlays, or spliced clips.
* **Timing Changes**: Detects if the video was trimmed, cut short, or sped up.
* **Quality Changes**: Detects if the video resolution was scaled down or resized (for example, from 1080p to 480p).
* **Audio Changes**: Detects if the audio track was muted, removed, swapped with different sound, or added to a video that was originally silent.

*(Note: Normal video compression from re-saving or sharing a video won't trigger a false alarm.)*

---

## Project Structure

```text
TrueCopy/
├── backend/               # Python server that processes the videos
│   ├── main.py            # API routes (/register and /verify)
│   ├── analyzer.py        # Compares videos and decides if they were altered
│   ├── fingerprint.py     # Scans video frames and audio to create a "fingerprint"
│   └── frame_extract.py   # Pulls frames from uploaded videos
├── frontend/              # Web interface (React)
│   └── src/
│       ├── App.tsx        # Main page layout
│       └── assets/Body.tsx# File upload box and results display
├── testing_guide.md       # Guide on how to create test videos using FFmpeg
└── test-checks.ps1        # Script to automatically test multiple videos at once
```

---

## How to Run It

### 1. Start the Backend (Python)
Open a terminal, go into the `backend` folder, and install the required packages:
```bash
cd backend
pip install fastapi uvicorn opencv-python numpy pillow imagehash imageio-ffmpeg
```
Start the backend server:
```bash
uvicorn main:main --reload
```

### 2. Start the Frontend (Web App)
Open a second terminal, go into the `frontend` folder, install the packages, and start the web app:
```bash
cd frontend
npm install
npm run dev
```
Then open the local link shown in your terminal (usually `http://localhost:5173`) in your browser.

---

## How to Use It

1. Switch to the **Register** tab and upload your original, unedited video.
2. Switch to the **Verify** tab and upload a video you want to check. TrueCopy will show you a similarity score and tell you if the visuals, timing, quality, or audio were changed.

### Using the Command Line (Optional)
You can also use `curl` instead of the web interface:

**Register a video:**
```bash
curl -X POST "http://localhost:8000/register" -F "file=@original.mp4"
```

**Verify a video:**
```bash
curl -X POST "http://localhost:8000/verify" -F "file=@edited_copy.mp4"
```

---

## Testing

If you want to generate test videos (like trimmed clips, resolution changes, or audio swaps) to see how TrueCopy catches them, check out `testing_guide.md` or run the PowerShell test script:
```powershell
./test-checks.ps1
```
Additionally, if you want to generate all the altered test footages using the original video, you could generate it yourself by using the <a href="https://github.com/ffmpeg/ffmpeg">ffmpeg</a> library
```bash
# 1. Benign Transcode (Compression / Bitrate change)
ffmpeg -y -i "15Seconds-DEMO.mp4" -c:v libx264 -crf 28 -c:a copy "test_transcode.mp4"

# 2. Quality / Downscale (Resizes 1080p -> 480p)
ffmpeg -y -i "15Seconds-DEMO.mp4" -vf "scale=-2:480" -c:v libx264 -crf 20 -c:a copy "test_resolution.mp4"

# 3. Temporal Cut / Trim (Drops the first 3.0 seconds)
ffmpeg -y -ss 00:00:03 -i "15Seconds-DEMO.mp4" -c copy "test_trim.mp4"

# 4. Spliced Tamper (Red box overlay from 4.0s to 7.0s)
ffmpeg -y -i "15Seconds-DEMO.mp4" -vf "drawbox=x=iw/4:y=ih/4:w=iw/2:h=ih/2:color=red@1.0:t=fill:enable='between(t,4.0,7.0)'" -c:v libx264 -crf 18 -c:a copy "test_splice.mp4"

# 5. Speed Alteration (Sped up by 1.25x -> shorter duration)
ffmpeg -y -i "15Seconds-DEMO.mp4" -filter_complex "[0:v]setpts=0.8*PTS[v];[0:a]atempo=1.25[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 "test_speed.mp4"

# 6. Watermark Banner (Yellow bar across the top-center from 4.0s to 9.0s)
ffmpeg -y -i "15Seconds-DEMO.mp4" -vf "drawbox=x=iw/6:y=ih/6:w=2*iw/3:h=120:color=yellow@1.0:t=fill:enable=gte(t\,4)*lte(t\,9)" -c:v libx264 -crf 18 -c:a copy "test_watermark.mp4"

# 7. Colorgrade / Negative Invert (Photo-negative effect from 5.0s to 10.0s)
ffmpeg -y -i "15Seconds-DEMO.mp4" -vf "split[v1][v2];[v2]negate[neg];[v1][neg]overlay=enable=gte(t\,5)*lte(t\,10)" -c:v libx264 -crf 18 -c:a copy "test_colorgrade.mp4"

# 8. Aspect Ratio Reframe / Crop (Center-crop to 9:16 vertical)
ffmpeg -y -i "15Seconds-DEMO.mp4" -vf "crop=ih*9/16:ih" -c:v libx264 -crf 18 -c:a copy "test_crop_reframe.mp4"

# 9. Censor Blur / Heavy Mosaic (Pixelation block active from 3.0s to 8.0s)
ffmpeg -y -i "15Seconds-DEMO.mp4" -filter_complex "[0:v]split[base][blur];[blur]scale=iw/16:ih/16,scale=1920:1080:flags=neighbor[pix];[base][pix]overlay=enable=gte(t\,3)*lte(t\,8)" -c:v libx264 -crf 18 -c:a copy "test_censor_blur.mp4"

# 10. Mid-Video Freeze Frame (Freezes at 4.0s for 3.0 seconds)
ffmpeg -y -i "15Seconds-DEMO.mp4" -filter_complex "[0:v]split=2[v1][v2];[v1]trim=0:4,setpts=PTS-STARTPTS[p1];[v2]trim=4:15,setpts=PTS-STARTPTS[p2];[p1]tpad=stop_mode=clone:stop_duration=3[frozen];[frozen][p2]concat=n=2:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 18 "test_freeze.mp4"

# 11. Audio Replacement (Replaces audio stream with a 440Hz tone, video unaltered)
ffmpeg -y -i "15Seconds-DEMO.mp4" -f lavfi -i "sine=frequency=440:duration=15" -map 0:v -map 1:a -c:v libx264 -crf 18 -c:a aac -shortest "test_audio_swap.mp4"
```

# AI Usage
*```No AI was used for this section of the file.```* - <a href="https://github.com/TheTHINGYEEE">thingy</a>


Commit names with the ```asked AI:``` prefix before it states that the code had some revisions / overhauls done by AI.

**Note that, we only used AI when we really needed it.** 
The website's concept design was entirely done on Figma by <a href="https://github.com/diogress">diogress</a>. And later done on TailwindCSS and React by <a href="https://github.com/TheTHINGYEEE">thingy</a>. 

So while it may look like AI, you can refer to <a href="https://github.com/diogress">diogress</a> for documentation on his Figma work.

**Documented AI Usage**:
1. Backend implementation such as making the algorithm for the perceptual hashing: the given frames, and complete audio alteration detection detection
2. Fix for frontend design responsiveness mainly for better display on mobile devices
3. Generate alterations of provided video file using <a href="https://github.com/ffmpeg/ffmpeg">ffmpeg</a> for easier testing
4. Mainly for bug fixing and knowing how to make the program work effectively

AI chatbots used: <a href="https://claude.ai>">Claude</a>, <a href="https:/gemini.google.com/">Google Gemini</a><br>
The project is under the category of <a href="https://en.wikipedia.org/wiki/AI-assisted_software_development">**AI-assisted development**</a>.

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the [GNU General Public License](LICENSE) for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

