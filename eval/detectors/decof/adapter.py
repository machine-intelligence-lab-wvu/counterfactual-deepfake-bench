"""DeCoF (Ma et al., arXiv 2402.02085) with the AIGVDBench release checkpoint.

Model code is the authors' own (github.com/LongMa-2025/DeCoF @ 5f73e8dc), used from a pinned
checkout under $FAIRDEEP_EXT/src_DeCoF rather than copied: frozen OpenAI CLIP ViT-L/14 image
encoder per frame -> 8 x 768 features -> 2-layer temporal transformer (`vit.ViT`) -> 2 logits.
The checkpoint holds only the temporal transformer (`model` key), exactly what the authors'
test.py loads into `Detector.net_all`.

Training data: the released DeCoF checkpoint is most likely trained on AIGVDBench's Open-Sora
split (per the paper's default training set and the checkpoint name); our generators are
therefore likely unseen. Not confirmed by the authors.

Preprocessing (applied on top of the view), from AIGVDBench (arXiv 2601.11035) section 7:
  "uniformly sampling 32 frames from its first 128 frames (or all available frames if the
  total is fewer than 128)", "center-cropped along the shorter side and resized to 256x256",
  saved as PNG (lossless), and "only the first 8 of the 32 sampled frames are used".
Then the authors' test transform (DeCoF src/utils/data.py, phase='test'):
  Resize((224, 224)) -> CenterCrop(224) -> ToTensor -> Normalize(ImageNet mean/std).
Score = softmax(logits)[:, 1] (test.py). The authors' decision is argmax over the two
logits, i.e. score >= 0.5.

Choices the sources leave open (recorded in eval/LOG.md):
  - "uniformly sample 32 of n" = np.linspace(0, n - 1, 32) floored; for n = 128 this gives
    frames 0, 4, ..., 28 for the first 8, identical to the DeCoF README rule ("first 32 frames,
    evenly select 8").
  - 256x256 resize uses PIL bilinear (the paper does not name the filter).
  - fp32 throughout, as in the authors' code (CLIP loaded on CPU in fp32); TF32 disabled.
"""
import os
import sys

import numpy as np
import torch

from eval.common import EXT, WEIGHTS, canonical_hash, sha256_file
from eval.detectors.base import Detector

SRC = os.path.join(EXT, "src_DeCoF", "src")
SRC_COMMIT = "5f73e8dc4f8cd9faeed07d767c9517e3f2c66044"
CKPT = os.path.join(WEIGHTS, "Weights", "DeCoF.tar")
CKPT_SHA = "4edb7b310cc729771e74b93f658c7fdc4f2e31fdfa617a88372a540d4f9e7b4a"
CLIP = os.path.join(WEIGHTS, "clip", "ViT-L-14.pt")
CLIP_SHA = "b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836"

SPEC = {
    "source": "AIGVDBench section 7 + DeCoF src/utils/data.py (test phase)",
    "frames_window": 128,
    "frames_sampled": 32,
    "frames_used": 8,
    "sampling": "np.linspace(0, n-1, 32).astype(int)[:8], n = min(128, frames)",
    "crop": "centre square, side = shorter side",
    "resize_1": [256, 256, "PIL.BILINEAR"],
    "intermediate_format": "lossless (PNG-equivalent, kept in memory)",
    "resize_2": [224, 224, "torchvision Resize default (bilinear, antialias)"],
    "centre_crop": 224,
    "normalize": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]},
    "backbone": "OpenAI CLIP ViT-L/14 (frozen), fp32",
    "head": "DeCoF vit.ViT(num_patches=8, dim=768, depth=2, heads=4, mlp_dim=768, pool=mean)",
    "score": "softmax(logits)[:, 1]",
    "precision": "fp32, TF32 off",
    "code": f"LongMa-2025/DeCoF@{SRC_COMMIT}",
    "clip_sha256": CLIP_SHA,
}


def sample_indices(n_frames, window=128, n_sample=32, n_use=8):
    n = min(window, n_frames)
    if n < n_use:
        raise ValueError(f"only {n_frames} frames")
    return np.linspace(0, n - 1, n_sample).astype(int)[:n_use]


class DeCoF(Detector):
    name = "decof"
    version = f"1+{canonical_hash(SPEC, 8)}"
    checkpoint_sha256 = CKPT_SHA
    preprocess_spec = SPEC
    default_threshold = 0.5
    threshold_source = "official: argmax over 2 logits (DeCoF test.py) == softmax[:,1] >= 0.5"
    report_note = (
        "The released DeCoF checkpoint is most likely trained on AIGVDBench's Open-Sora split "
        "(per the paper's default training set and the checkpoint name); our generators are "
        "therefore likely unseen. Not confirmed by the authors. Our curated GenBuster subset "
        "includes LTX-Video and HunyuanVideo, which are separate from DeCoF's training data but "
        "not from AIGVDBench as a whole.")

    def __init__(self):
        from torchvision import transforms
        self.tf = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(mean=SPEC["normalize"]["mean"], std=SPEC["normalize"]["std"]),
        ])
        self.device = None

    # ------------------------------------------------------------------ CPU side
    def prepare(self, path):
        import av
        from PIL import Image
        with av.open(path) as c:
            s = c.streams.video[0]
            n_hdr = s.frames
            frames = []
            for fr in c.decode(s):
                frames.append(fr)
                if len(frames) >= 128:
                    break
        idx = sample_indices(len(frames) if not n_hdr else min(n_hdr, len(frames)))
        out = torch.empty(8, 3, 224, 224)
        for k, i in enumerate(idx):
            img = frames[i].to_image()                     # RGB PIL
            w, h = img.size
            m = min(w, h)
            left, top = (w - m) // 2, (h - m) // 2
            img = img.crop((left, top, left + m, top + m)).resize((256, 256), Image.BILINEAR)
            out[k] = self.tf(img)
        return out

    # ------------------------------------------------------------------ GPU side
    def load(self, device):
        for p, want in [(CKPT, CKPT_SHA), (CLIP, CLIP_SHA)]:
            if sha256_file(p) != want:
                raise RuntimeError(f"checksum mismatch: {p}")
        if SRC not in sys.path:
            sys.path.insert(0, SRC)
        from clip import clip      # authors' vendored OpenAI CLIP
        from vit import ViT
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        clip_model, _ = clip.load(CLIP, device="cpu")    # fp32, as in clip_models.CLIPModel
        self.clip = clip_model.to(device).eval()
        self.head = ViT().to(device).eval()
        sd = torch.load(CKPT, map_location="cpu", weights_only=True)["model"]
        self.head.load_state_dict(sd)
        self.device = device
        return self

    @torch.no_grad()
    def score(self, batch):
        b = batch.shape[0]
        x = batch.to(self.device, non_blocking=True).float().flatten(0, 1)   # (b*8, 3, 224, 224)
        feats = self.clip.encode_image(x).float().view(b, 8, 768)
        logits = self.head(feats)
        return logits.softmax(1)[:, 1].float().cpu()
