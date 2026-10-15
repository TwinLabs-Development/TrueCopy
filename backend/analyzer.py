import numpy as np

MATCH_MAX = 10          # Compression noise ceiling
TAMPER_MIN = 12         # Macro visual tamper limit
TILE_TAMPER_LIMIT = 8   # Localized 3x3 quadrant tamper limit
AUDIO_TAMPER_MIN = 14   # Per-window 64-bit audio hash tamper limit
UNRELATED_MIN = 20      # Divergence ceiling before declaring unlinked
CONSECUTIVE_MIN = 2     # Minimum streak to record a segment
MAX_GAP_FRAMES = 1      # Allow up to 1 normal frame between anomalies before breaking streak


def audio_distance(a_fp: dict | None, b_fp: dict | None) -> int:
    """Computes phase-tolerant Hamming distance (0..64) between two audio window fingerprints."""
    if not a_fp or not b_fp:
        return 0
    a_has = bool(a_fp.get("has_audio", False))
    b_has = bool(b_fp.get("has_audio", False))
    if not a_has and not b_has:
        return 0
    if a_has != b_has:
        return 64

    a_silent = bool(a_fp.get("silent", False))
    b_silent = bool(b_fp.get("silent", False))
    if a_silent and b_silent:
        return 0
    if a_silent != b_silent:
        return 64

    a_bits = a_fp.get("bits")
    b_bits = b_fp.get("bits")
    if a_bits is None or b_bits is None:
        return 0

    b_shifts = b_fp.get("shifted_bits") or [b_bits]
    return min(int(np.count_nonzero(a_bits != b_s)) for b_s in b_shifts)


def best_alignment(orig, cand):
    """Slide cand over orig, returning the shift with the lowest average distance."""
    n, m = len(orig), len(cand)
    if n == 0 or m == 0:
        return None

    min_overlap = max(3, min(n, m) // 2)
    best = None

    for shift in range(-(m - 1), n):
        pairs = [(orig[j + shift], cand[j]) for j in range(m) if 0 <= j + shift < n]
        if len(pairs) < min_overlap:
            continue
        dists = [a["hash"] - b["hash"] for a, b in pairs]
        if not dists:
            continue
        avg = sum(dists) / len(dists)
        if best is None or avg < best[0]:
            best = (avg, pairs, dists)
    return best


def not_registered(avg, message, dur_delta=0.0):
    similarity = round(max(0.0, 100 - (avg / 64) * 100), 1)
    time_altered = dur_delta > 1.0
    return {
        "verdict": "not_registered",
        "avg_distance": float(avg),
        "overall_similarity": similarity,
        "is_authentic": False,
        "alterations": {
            "visually_altered": {
                "detected": True,
                "segments": [],
                "flagged_timestamps": [],
                "details": "Content diverges too significantly to link to baseline.",
            },
            "time_altered": {
                "detected": time_altered,
                "details": f"Duration mismatch of {dur_delta:.2f}s." if time_altered else "Comparable duration.",
            },
            "quality_altered": {
                "detected": False,
                "details": "Cannot verify resolution on unlinked video.",
            },
            "audio_altered": {
                "detected": False,
                "segments": [],
                "flagged_timestamps": [],
                "details": "Cannot verify audio on unlinked video.",
            },
        },
        "frames": [],
        "message": message,
    }


def compare(orig_meta, orig, cand_meta, cand):
    dur_delta = float(abs(orig_meta.get("duration_ms", 0) - cand_meta.get("duration_ms", 0)) / 1000)

    if not orig or not cand:
        return not_registered(64.0, "Zero frames available for comparison.", dur_delta)

    best = best_alignment(orig, cand)
    if best is None:
        return not_registered(64.0, "Not enough overlapping frames with registered original.", dur_delta)

    avg, pairs, dists = best
    avg = float(avg)

    matched_frac = sum(d <= MATCH_MAX for d in dists) / len(dists) if dists else 0.0
    if avg > UNRELATED_MIN or matched_frac < 0.3:
        return not_registered(
            avg,
            "Video diverges from registered original or is too heavily edited.",
            dur_delta,
        )

    frames = []
    flagged = []
    altered_segments = []

    # Visual streak state with gap tolerance
    streak_active = False
    streak_start = None
    streak_last = None
    tampered_frame_count = 0
    current_gap = 0

    # Audio streak state with gap tolerance
    audio_dists = []
    audio_flagged = []
    audio_segments = []
    a_streak_active = False
    a_streak_start = None
    a_streak_last = None
    a_tampered_count = 0
    a_current_gap = 0

    for (a, b), global_d in zip(pairs, dists):
        global_d = int(global_d)

        # Tile-by-tile comparison
        max_tile_dist = 0
        if "tile_hashes" in a and "tile_hashes" in b and a["tile_hashes"] and b["tile_hashes"]:
            tile_dists = [th1 - th2 for th1, th2 in zip(a["tile_hashes"], b["tile_hashes"])]
            max_tile_dist = max(tile_dists)

        is_tampered = (global_d > TAMPER_MIN) or (max_tile_dist > TILE_TAMPER_LIMIT)
        t_sec = f"{b['t_ms'] / 1000:.2f}"

        # Audio window comparison
        a_dist = audio_distance(a.get("audio_fp"), b.get("audio_fp"))
        audio_dists.append(a_dist)
        is_audio_tampered = a_dist > AUDIO_TAMPER_MIN

        frame_data = {
            "timestamp_sec": t_sec,
            "distance": global_d,
            "max_tile_distance": max_tile_dist,
            "audio_distance": a_dist,
            "matched": not is_tampered,
            "audio_matched": not is_audio_tampered,
            "frame_url": b.get("url", ""),
        }
        frames.append(frame_data)

        if is_tampered:
            flagged.append(frame_data)
            tampered_frame_count += 1
            current_gap = 0
            if not streak_active:
                streak_active = True
                streak_start = t_sec
            streak_last = t_sec
        else:
            if streak_active:
                current_gap += 1
                if current_gap > MAX_GAP_FRAMES:
                    if tampered_frame_count >= CONSECUTIVE_MIN:
                        altered_segments.append({
                            "start": f"{streak_start}s",
                            "end": f"{streak_last}s",
                            "frames_count": tampered_frame_count,
                        })
                    streak_active = False
                    streak_start = None
                    streak_last = None
                    tampered_frame_count = 0
                    current_gap = 0

        if is_audio_tampered:
            audio_flagged.append(frame_data)
            a_tampered_count += 1
            a_current_gap = 0
            if not a_streak_active:
                a_streak_active = True
                a_streak_start = t_sec
            a_streak_last = t_sec
        else:
            if a_streak_active:
                a_current_gap += 1
                if a_current_gap > MAX_GAP_FRAMES:
                    if a_tampered_count >= CONSECUTIVE_MIN:
                        audio_segments.append({
                            "start": f"{a_streak_start}s",
                            "end": f"{a_streak_last}s",
                            "frames_count": a_tampered_count,
                        })
                    a_streak_active = False
                    a_streak_start = None
                    a_streak_last = None
                    a_tampered_count = 0
                    a_current_gap = 0

    # Catch trailing visual streak
    if streak_active and tampered_frame_count >= CONSECUTIVE_MIN:
        altered_segments.append({
            "start": f"{streak_start}s",
            "end": f"{streak_last}s",
            "frames_count": tampered_frame_count,
        })

    # Catch trailing audio streak
    if a_streak_active and a_tampered_count >= CONSECUTIVE_MIN:
        audio_segments.append({
            "start": f"{a_streak_start}s",
            "end": f"{a_streak_last}s",
            "frames_count": a_tampered_count,
        })

    offset_s = float((pairs[0][0]["t_ms"] - pairs[0][1]["t_ms"]) / 1000) if pairs else 0.0
    time_altered = bool(dur_delta > 1.0 or abs(offset_s) > 0.5)

    o_res = f'{orig_meta.get("width", 0)}x{orig_meta.get("height", 0)}'
    c_res = f'{cand_meta.get("width", 0)}x{cand_meta.get("height", 0)}'
    quality_altered = bool(o_res != c_res)

    # Evaluate audio tampering across full track and localized segments
    orig_has_audio = orig_meta.get("has_audio", True)
    cand_has_audio = cand_meta.get("has_audio", True)
    avg_audio_dist = float(sum(audio_dists) / len(audio_dists)) if audio_dists else 0.0
    audio_flagged_frac = (len(audio_flagged) / len(pairs)) if pairs else 0.0

    if orig_has_audio and not cand_has_audio:
        audio_altered = True
        audio_details = "Audio track missing or muted compared to baseline."
    elif not orig_has_audio and cand_has_audio:
        audio_altered = True
        audio_details = "Unexpected audio track added to silent baseline."
    elif not orig_has_audio and not cand_has_audio:
        audio_altered = False
        audio_details = "No audio stream in baseline or candidate."
    elif audio_flagged_frac >= 0.5:
        audio_altered = True
        audio_details = (
            f"Audio track swapped or replaced ({len(audio_flagged)}/{len(pairs)} windows altered, "
            f"avg distance: {avg_audio_dist:.1f})."
        )
    elif len(audio_segments) > 0:
        audio_altered = True
        audio_details = (
            f"{len(audio_flagged)} audio window(s) altered across {len(audio_segments)} segment(s)."
        )
    else:
        audio_altered = False
        audio_details = "Audio matches baseline."

    similarity = round(max(0.0, 100 - (avg / 64) * 100), 1)
    is_authentic = (
        len(flagged) == 0
        and not time_altered
        and not quality_altered
        and not audio_altered
    )

    return {
        "verdict": "authentic" if is_authentic else "altered",
        "avg_distance": avg,
        "overall_similarity": similarity,
        "is_authentic": is_authentic,
        "alterations": {
            "visually_altered": {
                "detected": bool(flagged),
                "segments": altered_segments,
                "flagged_timestamps": [f'{f["timestamp_sec"]}s' for f in flagged],
                "details": f"{len(flagged)} frame(s) altered across {len(altered_segments)} segment(s)."
                if flagged
                else "No visual anomalies detected.",
            },
            "time_altered": {
                "detected": time_altered,
                "details": f"Duration delta: {dur_delta:.2f}s, offset: {offset_s:+.2f}s."
                if time_altered
                else "Timing matches baseline.",
            },
            "quality_altered": {
                "detected": quality_altered,
                "details": f"Resolution scaled: {o_res} -> {c_res}." if quality_altered else "Native resolution intact.",
            },
            "audio_altered": {
                "detected": audio_altered,
                "segments": audio_segments,
                "flagged_timestamps": [f'{f["timestamp_sec"]}s' for f in audio_flagged],
                "details": audio_details,
            },
        },
        "frames": frames,
    }