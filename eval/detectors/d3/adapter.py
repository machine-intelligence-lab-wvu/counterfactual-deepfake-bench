"""D3 (Zheng et al., ICCV 2025, arXiv 2508.00701): training-free detection from second-order
features. Code: github.com/Zig-HS/D3 @ c798fbc (MIT); re-implemented here from models/D3_model.py,
data/datasets.py and utils/video2frame.py, nothing trained.

Method (official default, eval.py: --encoder XCLIP-16 --loss l2): embed 16 consecutive frames
with the X-CLIP-B/16 vision tower (pooler_output per frame), take the L2 distance between
consecutive embeddings (15 values), their first differences (14 values, the "second-order"
feature), and the standard deviation of those. Real video has the larger spread: the authors'
AP treats real as the positive class with the raw std as its score.

Score in [0, 1], higher = more likely generated: 1 / (1 + std). Strictly decreasing in std, so
every rank metric (AUC, AP, EER, TPR at a calibrated FPR) is the authors' statistic unchanged;
std = 1 / score - 1 recovers it. There is no official decision threshold: the 0.5 provisional
threshold is arbitrary for D3 and only the calibrated (5% real FPR) threshold is meaningful.

Preprocessing (applied on top of the view), as in the official pipeline:
  - utils/video2frame.py: `ffmpeg -ss <start> -t 3 -i video -vf fps=8 %d.jpg` (JPEG, ffmpeg's
    default mjpeg settings); start is random in the authors' code, 0 here (the view has already
    chosen the segment: fakes from their start, reals from their middle);
  - data/datasets.py: the first 16 frames (8 if 8-15 exist; fewer is an error), cv2.imread
    (BGR, no conversion), centre crop trimming 10% off each side of the longer dimension,
    albumentations Resize(224, 224) (cv2 INTER_LINEAR), ImageNet mean/std on 0-255;
  - fp32 (no autocast in eval.py); TF32 off here.
"""
import glob
import os
import subprocess
import tempfile

import numpy as np
import torch

from eval.common import FFMPEG, WEIGHTS, canonical_hash, sha256_file
from eval.detectors.base import Detector

SRC_COMMIT = "c798fbc57fe0c4198d63a73732c2c0f9e4b4816c"
XCLIP_DIR = os.path.join(WEIGHTS, "xclip-base-patch16")
XCLIP_REV = "d6184e3fd8780d04c85d0f1eabe5f94bf44d98f6"
XCLIP_SHA = "b5db836d57b7e22001cb2bab581719e910b4c571d926fe839b5d07bc0ba2d03e"

FPS = 8
CLIP_S = 3
IMG_SIZE = 224
CROP_PCT = 0.10
MEAN = np.array([0.485, 0.456, 0.406], np.float32) * 255.0
STD = np.array([0.229, 0.224, 0.225], np.float32) * 255.0

SPEC = {
    "source": f"Zig-HS/D3@{SRC_COMMIT} utils/video2frame.py + data/datasets.py + models/D3_model.py",
    "frames": f"ffmpeg -t {CLIP_S} -vf fps={FPS} -> JPEG (ffmpeg default mjpeg), from view start",
    "frames_used": "first 16 (8 if 8-15 available)",
    "channels": "BGR (cv2.imread, as in the official dataset)",
    "crop": "centre, trim 10% each side of the longer dimension",
    "resize": [IMG_SIZE, IMG_SIZE, "cv2.INTER_LINEAR"],
    "normalize": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225],
                  "max_pixel_value": 255},
    "encoder": f"microsoft/xclip-base-patch16@{XCLIP_REV} vision tower, pooler_output",
    "statistic": "std of first differences of consecutive-frame L2 distances (loss l2)",
    "score": "1 / (1 + std)",
    "precision": "fp32, TF32 off",
}


def second_order_std(emb):
    """emb: (b, t, d) frame embeddings -> (b,) std of the second-order L2 feature."""
    d1 = torch.norm(emb[:, 1:] - emb[:, :-1], p=2, dim=-1)       # (b, t-1)
    d2 = d1[:, 1:] - d1[:, :-1]                                   # (b, t-2)
    return torch.std(d2, dim=1)                                   # ddof=1, as in D3_model.py


class D3(Detector):
    name = "d3"
    version = f"1+{canonical_hash(SPEC, 8)}"
    checkpoint_sha256 = XCLIP_SHA
    preprocess_spec = SPEC
    default_threshold = 0.5
    threshold_source = ("none official (training-free statistic); 0.5 on 1/(1+std) is arbitrary - "
                        "use the calibrated threshold")
    report_note = (
        "D3 is training-free: a statistic of frozen X-CLIP-B/16 features, no detector weights. "
        "Its score is 1/(1+std) of the second-order feature; only rank metrics and the calibrated "
        "threshold are meaningful, the provisional 0.5 threshold is not.")

    def __init__(self):
        self.device = None

    # ------------------------------------------------------------------ CPU side
    def _frame(self, path):
        import cv2
        img = cv2.imread(path)
        h, w = img.shape[:2]
        if w > h:
            p = int(w * CROP_PCT)
            img = img[:, p:w - p]
        else:
            p = int(h * CROP_PCT)
            img = img[p:h - p, :]
        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_LINEAR)
        return ((img.astype(np.float32) - MEAN) / STD).transpose(2, 0, 1)

    def prepare(self, path):
        with tempfile.TemporaryDirectory(prefix="d3_") as tmp:
            r = subprocess.run([FFMPEG, "-nostdin", "-loglevel", "error", "-t", str(CLIP_S),
                                "-i", path, "-vf", f"fps={FPS}", os.path.join(tmp, "%d.jpg")],
                               capture_output=True, text=True)
            if r.returncode:
                raise RuntimeError(f"ffmpeg: {r.stderr.strip()[-300:]}")
            files = sorted(glob.glob(os.path.join(tmp, "*.jpg")),
                           key=lambda p: int(os.path.basename(p).split(".")[0]))
            if len(files) < 8:
                raise RuntimeError(f"only {len(files)} frames at {FPS} fps")
            n = 8 if len(files) < 16 else 16
            return torch.from_numpy(np.stack([self._frame(f) for f in files[:n]]))

    # ------------------------------------------------------------------ GPU side
    def load(self, device):
        if sha256_file(os.path.join(XCLIP_DIR, "model.safetensors")) != XCLIP_SHA:
            raise RuntimeError(f"checksum mismatch: {XCLIP_DIR}/model.safetensors")
        from safetensors.torch import load_file
        from transformers import XCLIPConfig, XCLIPVisionModel
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        # transformers 5.x XCLIPVisionModel.from_pretrained on the full X-CLIP checkpoint does
        # not map `vision_model.*` and silently random-initialises the whole tower (4.57, the
        # authors' version, did). Load the tower's tensors explicitly and strictly.
        enc = XCLIPVisionModel(XCLIPConfig.from_pretrained(XCLIP_DIR).vision_config)
        sd = load_file(os.path.join(XCLIP_DIR, "model.safetensors"))
        want = set(enc.state_dict())
        sub = {}
        for k, v in sd.items():
            if k.startswith("vision_model."):
                k2 = k[len("vision_model."):]
                sub[k2 if k2 in want else "vision_model." + k2] = v
        missing, unexpected = enc.load_state_dict(sub, strict=False)
        missing = [k for k in missing if not k.endswith("position_ids")]       # a buffer
        unexpected = [k for k in unexpected if not k.endswith("position_ids")]
        if missing or unexpected:
            raise RuntimeError(f"X-CLIP vision tower: missing {missing[:5]}, unexpected {unexpected[:5]}")
        self.encoder = enc.to(device).eval()
        self.device = device
        return self

    @torch.no_grad()
    def score(self, batch):
        x = batch.to(self.device, non_blocking=True).float()
        b, t = x.shape[:2]
        emb = self.encoder(x.flatten(0, 1)).pooler_output.float().view(b, t, -1)
        return (1.0 / (1.0 + second_order_std(emb))).cpu()
