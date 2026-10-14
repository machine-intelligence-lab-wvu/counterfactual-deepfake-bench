"""Face-count gate (plan 7.1 "exactly one face") with OpenCV YuNet.

Samples frames evenly across the whole clip, detects faces, and treats the
largest face per frame as the subject. Everything else is a secondary face,
measured by its height relative to the subject so that small, distant
background figures (a known Wan 4-step failure in indoor scenes) can be told
apart from a second prominent person.

Calibrated by eye on 16 Wan clips (2026-10-14). False positives at low score
were wallpaper flowers and drawn faces on classroom posters (max score
0.70-0.71); real background people scored 0.80-0.90 (max per clip). A profile
subject's ear was detected as a second face overlapping the subject box. Hence:
a secondary face counts only if it does not overlap the subject, scores
>= PERSON_SCORE, and shows up in >= BG_MIN_FRAMES sampled frames. On the
calibration set this flags all 4 clips with visible background people and none
of the 3 decor/ear false positives. Recall is limited by YuNet itself: very
small or back-turned figures are not detected, so treat face_pass as a lower
bound on contamination, not a guarantee.

The model (opencv/face_detection_yunet, 2023mar fp32, ~230 KB) is fetched from
Hugging Face on first use and cached.
"""
import numpy as np

REPO, FILE = "opencv/face_detection_yunet", "face_detection_yunet_2023mar.onnx"
SCORE = 0.6          # detector floor; YuNet default 0.9 misses small background faces
PERSON_SCORE = 0.75  # secondary faces below this were decor, not people
MIN_FACE_PX = 12     # below this YuNet output is noise at 1280x704
BG_MIN_FRAMES = 1    # of the sampled frames; 2 missed a real case (partly occluded people)
_det = {}


def detector(w, h):
    import cv2
    if "d" not in _det:
        from huggingface_hub import hf_hub_download
        _det["d"] = cv2.FaceDetectorYN.create(hf_hub_download(REPO, FILE), "",
                                              (w, h), SCORE, 0.3, 5000)
    d = _det["d"]
    d.setInputSize((w, h))
    return d


def analyse(frames_rgb, n_sample=8):
    """frames_rgb: list of HxWx3 uint8. Returns per-clip face statistics."""
    import cv2
    idx = np.linspace(0, len(frames_rgb) - 1, min(n_sample, len(frames_rgb))).round().astype(int)
    h, w = frames_rgb[0].shape[:2]
    det = detector(w, h)
    no_face, rel_secondary, n_people, subj_h, subj_cx = 0, [], [], [], []
    for i in idx:
        _, faces = det.detect(cv2.cvtColor(frames_rgb[i], cv2.COLOR_RGB2BGR))
        fs = [] if faces is None else sorted(
            (f for f in faces if f[3] >= MIN_FACE_PX), key=lambda f: -f[3])
        if not fs:
            no_face += 1
            n_people.append(0)
            rel_secondary.append(0.0)
            continue
        s = fs[0]
        others = [f for f in fs[1:] if f[-1] >= PERSON_SCORE and not _overlaps(f, s)]
        subj_h.append(s[3])
        subj_cx.append((s[0] + s[2] / 2) / w)
        n_people.append(len(others))
        rel_secondary.append(max(f[3] for f in others) / s[3] if others else 0.0)
    bg_frames = int((np.array(n_people) > 0).sum())
    return {
        "face_frames": len(idx),
        "face_none_frames": no_face,
        "face_bg_frames": bg_frames,
        "face_bg_max_count": int(max(n_people)),
        # largest extra person relative to the subject, over sampled frames
        "face_secondary_rel_max": round(float(max(rel_secondary)), 3),
        "face_subject_h": round(float(np.median(subj_h)), 1) if subj_h else 0.0,
        "face_subject_cx": round(float(np.median(subj_cx)), 3) if subj_cx else 0.0,
        "face_bg_people": int(bg_frames >= BG_MIN_FRAMES),
        # Background people only. "No face" is reported but not gated: on LTX it
        # fired on 82 clips, almost all backlit/low-light close-ups where a face
        # is plainly visible but too dark and large for YuNet (5 of 6 spot-checked).
        "face_pass": int(bg_frames < BG_MIN_FRAMES),
    }


def _overlaps(a, b):
    return not (a[0] > b[0] + b[2] or a[0] + a[2] < b[0] or
                a[1] > b[1] + b[3] or a[1] + a[3] < b[1])
