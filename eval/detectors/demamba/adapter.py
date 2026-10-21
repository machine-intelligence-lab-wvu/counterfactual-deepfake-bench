"""DeMamba (Chen et al., arXiv 2405.19707) with our own GenVideo-100K checkpoint.

Weights: Ahsanz/DeMamba-GenVideo100K@27468b8 `best_acc.pth` (epoch 15 of 30), trained by us
with a single-GPU adaptation of the authors' code (github.com/chenhaoxing/DeMamba): X-CLIP-B/16
vision encoder, fully fine-tuned, + bidirectional pure-PyTorch Mamba head, one logit. These are
NOT the authors' weights; the authors have not released any (DeMamba issue #16). Model code in
model.py comes from our standalone evaluator, which loads the checkpoint strictly.

Training data: GenVideo-100K (10K clips per forgery source: ZeroScope, I2VGen-XL, SVD,
VideoCrafter, Pika, DynamiCrafter, SD, SEINE, Latte, OpenSora; reals from Kinetics-400 and
Youku). None of our generators (LTX, Wan, HunyuanVideo) is in it. On the full GenVideo
validation set: accuracy 88.74%, AUC 96.67%, real recall 0.832 at 0.5.

Preprocessing (applied on top of the view), as in the authors' data pipeline
(Preprocess/video2frame.py + dataloader.py, validation phase) and our standalone evaluator:
  - frames at 2 fps for clips >= 4 s (else ceil(8 / duration) fps), every round(fps / 2)-th
    decoded frame, at most 32 kept; every view clip is 5.0 s, so always 2 fps;
  - the centre 8-frame window (training and the authors' validation pick a random window);
  - centre crop trimming 10% off each side of the longer dimension, resize to 224x224
    (cv2 INTER_LINEAR; albumentations.Resize default), ImageNet mean/std on 0-255 values;
  - BGR -> RGB (cv2.cvtColor), as in our training dataloader.
Score = sigmoid(logit); threshold 0.5 (standalone evaluator and training metrics).

Differences from training that the sources leave open (recorded in eval/LOG.md):
  - the authors extract frames with `ffmpeg -r 2` to JPEG; we sample decoded frames directly,
    so there is no JPEG round trip;
  - fp32 with TF32 off here; training used bf16 autocast.
"""
import math
import os

import numpy as np
import torch

from eval.common import WEIGHTS, canonical_hash, sha256_file
from eval.detectors.base import Detector

CKPT = os.path.join(WEIGHTS, "demamba", "best_acc.pth")
CKPT_SHA = "f89897c72b595aa85a524e59083919cebb0b92161d2a694a2cbffbdd8456ce17"
CKPT_REPO = "Ahsanz/DeMamba-GenVideo100K@27468b8201fc55978bbce51450949345867de184"

# RGB: our training dataloader converts OpenCV's BGR frames with cv2.cvtColor (confirmed
# 2026-10-21; the checkpoint README's "BGR channel order" line describes OpenCV's decode only).
CHANNELS = "RGB"

NUM_FRAMES = 8
MAX_FRAMES = 32
IMG_SIZE = 224
CROP_PCT = 0.10
MEAN = np.array([0.485, 0.456, 0.406], np.float32) * 255.0
STD = np.array([0.229, 0.224, 0.225], np.float32) * 255.0

SPEC = {
    "source": "DeMamba Preprocess/video2frame.py + dataloader.py (val) + our standalone evaluator",
    "sampling": "every round(fps/target)-th frame, target 2 fps (>= 4 s) else ceil(8/dur); "
                "max 32 kept",
    "window": "centre 8 consecutive sampled frames; zero-pad if fewer than 8",
    "crop": "centre, trim 10% each side of the longer dimension",
    "resize": [IMG_SIZE, IMG_SIZE, "cv2.INTER_LINEAR"],
    "channels": CHANNELS,
    "normalize": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225],
                  "max_pixel_value": 255},
    "model": "XCLIP_DeMamba (X-CLIP-B/16 vision, fine-tuned) + bidirectional Mamba, 1 logit",
    "score": "sigmoid(logit)",
    "precision": "fp32, TF32 off",
    "weights": CKPT_REPO,
}


def target_fps(duration):
    return 2 if duration >= 4 else math.ceil(8 / max(duration, 1.0))


def centre_start(n):
    return (n - NUM_FRAMES) // 2


class DeMamba(Detector):
    name = "demamba"
    version = f"1+{canonical_hash(SPEC, 8)}"
    checkpoint_sha256 = CKPT_SHA
    preprocess_spec = SPEC
    default_threshold = 0.5
    threshold_source = "sigmoid(logit) > 0.5 (training metrics and our standalone evaluator)"
    report_note = (
        "DeMamba weights are our own (GenVideo-100K, single-GPU adaptation of the authors' code), "
        "not an official release; the authors have published none. GenVideo-100K contains none "
        "of our generators. On GenVideo validation it flags 16.8% of real videos at 0.5.")

    def __init__(self):
        self.device = None

    # ------------------------------------------------------------------ CPU side
    def _frame(self, bgr):
        import cv2
        img = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]
        if w > h:
            p = int(w * CROP_PCT)
            img = img[:, p:w - p]
        else:
            p = int(h * CROP_PCT)
            img = img[p:h - p, :]
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_LINEAR)
        img = (img.astype(np.float32) - MEAN) / STD
        return img.transpose(2, 0, 1)

    def prepare(self, path):
        import cv2
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError("unreadable")
        fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
        total = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
        if fps <= 0 or total <= 0:
            cap.release()
            raise RuntimeError(f"bad header (fps={fps}, frames={total})")
        stride = max(1, int(round(fps / target_fps(total / fps))))
        # only the centre window is used, so decode no further than its last frame
        n_kept = min(MAX_FRAMES, (int(total) + stride - 1) // stride)
        last = centre_start(n_kept) + NUM_FRAMES if n_kept >= NUM_FRAMES else n_kept
        frames, i = [], 0
        while len(frames) < last:
            ok, fr = cap.read()
            if not ok:
                break
            if i % stride == 0:
                frames.append(fr)
            i += 1
        cap.release()
        if not frames:
            raise RuntimeError("no frames decoded")
        if len(frames) < last:            # header overstated the length: use what decoded
            n_kept = len(frames)
        if n_kept >= NUM_FRAMES:
            s = centre_start(n_kept)
            sel = [self._frame(f) for f in frames[s:s + NUM_FRAMES]]
        else:
            sel = [self._frame(f) for f in frames]
            sel += [np.zeros((3, IMG_SIZE, IMG_SIZE), np.float32)] * (NUM_FRAMES - len(sel))
        return torch.from_numpy(np.stack(sel))        # (8, 3, 224, 224)

    # ------------------------------------------------------------------ GPU side
    def load(self, device):
        if sha256_file(CKPT) != CKPT_SHA:
            raise RuntimeError(f"checksum mismatch: {CKPT}")
        from eval.detectors.demamba.model import XCLIP_DeMamba, load_checkpoint
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        model = XCLIP_DeMamba()
        load_checkpoint(model, CKPT)
        self.model = model.to(device).eval()
        self.device = device
        return self

    @torch.no_grad()
    def score(self, batch):
        x = batch.to(self.device, non_blocking=True).float()
        return self.model(x).float()[:, 0].sigmoid().cpu()
