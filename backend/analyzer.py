MATCH_MAX = 10      # <= this: same picture (compression noise)
TAMPER_MIN = 12     # > this: visually changed
UNRELATED_MIN = 20  # avg bits apart; above this it's a different video


def best_alignment(orig, cand):
    """Slide cand over orig, return the shift with the lowest average distance."""
    n, m = len(orig), len(cand)
    min_overlap = max(3, min(n, m) // 2)
    best = None
    for shift in range(-(m - 1), n):  # cand[j] pairs with orig[j + shift]
        pairs = [(orig[j + shift], cand[j]) for j in range(m) if 0 <= j + shift < n]
        if len(pairs) < min_overlap:
            continue
        avg = sum(a["hash"] - b["hash"] for a, b in pairs) / len(pairs)
        if best is None or avg < best[0]:
            best = (avg, pairs)
    return best


def not_registered(avg, message):
    return {
        "verdict": "not_registered",
        "avg_distance": avg,
        "overall_similarity": round(max(0.0, 100 - (avg / 64) * 100), 1),
        "is_authentic": False,
        "alterations": {},
        "frames": [],
        "message": message,
    }


def compare(orig_meta, orig, cand_meta, cand):
    best = best_alignment(orig, cand)
    if best is None:
        return not_registered(64, "Not enough overlap with the registered video.")

    avg, pairs = best
    matched_frac = sum(a["hash"] - b["hash"] <= MATCH_MAX for a, b in pairs) / len(pairs)
    if avg > UNRELATED_MIN or matched_frac < 0.3:
        return not_registered(
            avg,
            "This doesn't match any registered original. It may be unregistered, or too heavily edited to link.",
        )

    frames = []
    for a, b in pairs:
        d = a["hash"] - b["hash"]
        frames.append({
            "timestamp_sec": round(b["t_ms"] / 1000, 2),
            "distance": d,
            "matched": d <= MATCH_MAX,
            "frame_url": b["url"],
        })

    flagged = [f for f in frames if f["distance"] > TAMPER_MIN]
    offset_s = (pairs[0][0]["t_ms"] - pairs[0][1]["t_ms"]) / 1000
    dur_delta = abs(orig_meta["duration_ms"] - cand_meta["duration_ms"]) / 1000
    time_altered = dur_delta > 1.0 or abs(offset_s) > 0.5

    o_res = f'{orig_meta["width"]}x{orig_meta["height"]}'
    c_res = f'{cand_meta["width"]}x{cand_meta["height"]}'
    quality_altered = o_res != c_res

    similarity = round(max(0.0, 100 - (avg / 64) * 100), 1)
    is_authentic = not flagged and not time_altered

    return {
        "verdict": "authentic" if is_authentic else "altered",
        "avg_distance": avg,
        "overall_similarity": similarity,
        "is_authentic": is_authentic,
        "alterations": {
            "visually_altered": {
                "detected": bool(flagged),
                "flagged_timestamps": [f'{f["timestamp_sec"]}s' for f in flagged],
                "details": f"{len(flagged)} frame(s) showed visual tampering.",
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