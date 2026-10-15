MATCH_MAX = 10        # <= this: same picture (compression noise)
TAMPER_MIN = 12       # > this: visually changed
UNRELATED_MIN = 20    # avg bits apart; above this it's a different video
CONSECUTIVE_MIN = 2   # min consecutive flagged frames to declare a spliced/tampered scene
TILE_TAMPER_LIMIT = 8  # Max allowed difference on any single 3x3 quadrant


def best_alignment(orig, cand):
    """Slide cand over orig, return the shift with the lowest average distance."""
    n, m = len(orig), len(cand)
    min_overlap = max(3, min(n, m) // 2)
    best = None
    for shift in range(-(m - 1), n):  # cand[j] pairs with orig[j + shift]
        pairs = [(orig[j + shift], cand[j]) for j in range(m) if 0 <= j + shift < n]
        if len(pairs) < min_overlap:
            continue
        dists = [a["hash"] - b["hash"] for a, b in pairs]
        avg = sum(dists) / len(dists)
        if best is None or avg < best[0]:
            best = (avg, pairs, dists)
    return best


def not_registered(avg, message, dur_delta=0.0):
    similarity = round(max(0.0, 100 - (avg / 64) * 100), 1)
    time_altered = dur_delta > 1.0
    return {
        "verdict": "not_registered",
        "avg_distance": avg,
        "overall_similarity": similarity,
        "is_authentic": False,
        "alterations": {
            "visually_altered": {
                "detected": True,
                "segments": [],
                "flagged_timestamps": [],
                "details": "Video diverges significantly from baseline.",
            },
            "time_altered": {
                "detected": time_altered,
                "details": f"Duration mismatch of {dur_delta:.2f}s." if time_altered else "Duration comparable.",
            },
            "quality_altered": {
                "detected": False,
                "details": "Cannot verify resolution.",
            },
            "audio_altered": {"detected": False, "details": "Audio check not implemented yet."},
        },
        "frames": [],
        "message": message,
    }


def compare(orig_meta, orig, cand_meta, cand):
    best = best_alignment(orig, cand)
    dur_delta = float(abs(orig_meta["duration_ms"] - cand_meta["duration_ms"]) / 1000)

    if best is None:
        return not_registered(64, "Not enough overlap with the registered video.", dur_delta)

    avg, pairs, dists = best
    avg = float(avg)

    matched_frac = sum(d <= MATCH_MAX for d in dists) / len(dists)
    if avg > UNRELATED_MIN or matched_frac < 0.3:
        return not_registered(
            avg,
            "This doesn't match any registered original. It may be unregistered, or too heavily edited to link.",
            dur_delta,
        )

    frames = []
    altered_segments = []
    flagged = []
    spike_start = None
    spike_count = 0

    for idx, ((a, b), global_d) in enumerate(zip(pairs, dists)):
        global_d = int(global_d)

        # 3x3 Tile comparisons
        max_tile_dist = 0
        if "tile_hashes" in a and "tile_hashes" in b:
            tile_dists = [
                th1 - th2 for th1, th2 in zip(a["tile_hashes"], b["tile_hashes"])
            ]
            max_tile_dist = max(tile_dists)

        # Flag if macro energy changed OR a localized tile changed
        is_tampered = (global_d > TAMPER_MIN) or (max_tile_dist > TILE_TAMPER_LIMIT)
        t_sec = f"{b['t_ms'] / 1000:.2f}"

        frame_data = {
            "timestamp_sec": t_sec,
            "distance": global_d,
            "max_tile_distance": max_tile_dist,
            "matched": not is_tampered,
            "frame_url": b.get("url", ""),
        }
        frames.append(frame_data)

        if is_tampered:
            flagged.append(frame_data)
            if spike_count == 0:
                spike_start = t_sec
            spike_count += 1
        else:
            if spike_count >= CONSECUTIVE_MIN:
                prev_t_sec = f"{pairs[idx - 1][1]['t_ms'] / 1000:.2f}"
                altered_segments.append({
                    "start": f"{spike_start}s",
                    "end": f"{prev_t_sec}s",
                    "frames_count": spike_count,
                })
            spike_count = 0

    # Catch trailing streak
    if spike_count >= CONSECUTIVE_MIN:
        last_t_sec = f"{pairs[-1][1]['t_ms'] / 1000:.2f}"
        altered_segments.append({
            "start": f"{spike_start}s",
            "end": f"{last_t_sec}s",
            "frames_count": spike_count,
        })

    offset_s = float((pairs[0][0]["t_ms"] - pairs[0][1]["t_ms"]) / 1000)
    time_altered = bool(dur_delta > 1.0 or abs(offset_s) > 0.5)

    o_res = f'{orig_meta["width"]}x{orig_meta["height"]}'
    c_res = f'{cand_meta["width"]}x{cand_meta["height"]}'
    quality_altered = o_res != c_res

    similarity = round(max(0.0, 100 - (avg / 64) * 100), 1)
    is_authentic = len(flagged) == 0 and not time_altered

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
                "details": f"{len(flagged)} frame(s) showed visual tampering across {len(altered_segments)} segment(s).",
            },
            "time_altered": {
                "detected": time_altered,
                "details": f"Duration differs by {dur_delta:.2f}s, start offset {offset_s:+.2f}s.",
            },
            "quality_altered": {
                "detected": quality_altered,
                "details": f"Resolution {o_res} -> {c_res}." if quality_altered else "Same resolution.",
            },
            "audio_altered": {"detected": False, "details": "Audio check not implemented yet."},
        },
        "frames": frames,
    }