"""V-PVP (Cui et al., NeurIPS 2026, arXiv 2607.15321, "Rethinking the Readout"): a velocity-gated
patch readout (~0.5M parameters) on a frozen VideoMAE-B/16 fine-tuned on Kinetics-400.

Code: github.com/manic-cui/Rethinking-the-readout @ 6ca3b11 (MIT), used from the pinned copy in
mannicui0/Rethinking-the-readout @ 249f040 under $FAIRDEEP_WEIGHTS/vpvp (src/ is identical to the
GitHub commit): `src/pvp_head.py` (PVPHead) and `src/backbones/videomae_k400.py` (frozen VideoMAE
wrapper that remaps the checkpoint's attention q/v offsets to the installed transformers layout; all 182
tensors was checked equal to the checkpoint on transformers 5.20).

Head: `checkpoints/pvp_heads/videomae_k400_vpvp.pt`, trained with the backbone frozen on
AIGVDBench Real + Open-Sora + CogVideoX1.5 + EasyAnimate; mga AUC 0.9528 on the 20-generator
Open-Source test split (paper Table 1). Our generators (LTX 2.3, Wan 2.2, HunyuanVideo 1.5) are
not in its training set; AIGVDBench's test split contains LTX, Wan2.1 and HunyuanVideo versions.
Backbone: MCG-NJU/videomae-base-finetuned-kinetics @ 488eb9a.

Preprocessing (applied on top of the view):
  - AIGVDBench frame extraction (arXiv 2601.11035 section 7, as in the DeCoF adapter): 32 frames
    uniformly from the first 128 (np.linspace(0, n-1, 32), n = min(128, frames)), centre square
    crop, resize to 256x256 (PIL bilinear), lossless;
  - V-PVP src/dataset.py: 16 of those 32 frames at np.linspace(0, 31, 16, dtype=int), centre square
    crop (a no-op on 256x256), resize to 224x224 PIL BICUBIC, then the backbone's ImageNet mean/std
    (the official loader normalises with 0.45/0.225 and renormalises on the GPU; applied directly
    here);
  - backbone under fp16 autocast, head fp32 (src/eval_opensource.py).
Score = sigmoid(logit) computed in float64 (the official float32 sigmoid rounds every logit above
~17 to exactly 1.0, which on FairDeep tied 12% of reals and 10-14% of fakes at the top; the logits
reach ~28, inside float64's range); threshold 0.5 (eval_opensource.py `--threshold`).
"""
import os
import sys

import numpy as np
import torch

from eval.common import WEIGHTS, canonical_hash, sha256_file
from eval.detectors.base import Detector

SRC = os.path.join(WEIGHTS, "vpvp", "src")
SRC_COMMIT = "6ca3b1195c4b842c593638055bbcc9c8eaa6781d"
HF_REV = "249f040d5fc30fe6eadab54b9393dcc059a0d083"
HEAD = os.path.join(WEIGHTS, "vpvp", "checkpoints", "pvp_heads", "videomae_k400_vpvp.pt")
HEAD_SHA = "33581d50452bcf19373a3e5db1204e44b456cb216ac21a3b889ee6970ba6f93b"
BACKBONE = os.path.join(WEIGHTS, "videomae-base-finetuned-kinetics")
BACKBONE_REV = "488eb9a0565f257b32866000305c8178965eb9f6"
BACKBONE_SHA = "065cfde56f97671da4d196e1a3a6d3cf9304dcad92eb671e3632a6c6cdd04f73"

N_FRAMES = 16
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)

SPEC = {
    "source": f"manic-cui/Rethinking-the-readout@{SRC_COMMIT} src/dataset.py + eval_opensource.py; "
              "AIGVDBench section 7 frame extraction",
    "extraction": "32 of the first 128 frames, np.linspace(0, n-1, 32); centre square; 256x256 PIL bilinear",
    "frames_used": "np.linspace(0, 31, 16, dtype=int) of the 32",
    "resize": [224, 224, "PIL BICUBIC"],
    "normalize": {"mean": list(MEAN), "std": list(STD)},
    "backbone": f"MCG-NJU/videomae-base-finetuned-kinetics@{BACKBONE_REV}, frozen, last block, fp16 autocast",
    "head": f"PVPHead('velocity_gated', D=768), videomae_k400_vpvp.pt (sha {HEAD_SHA[:12]}), fp32",
    "score": "sigmoid(logit) in float64",
}


class VPVP(Detector):
    name = "vpvp"
    version = f"1+{canonical_hash(SPEC, 8)}"
    checkpoint_sha256 = HEAD_SHA
    preprocess_spec = SPEC
    default_threshold = 0.5
    threshold_source = "official: sigmoid(logit) > 0.5 (eval_opensource.py --threshold default)"
    report_note = (
        "V-PVP head trained by the authors on AIGVDBench Real + Open-Sora + CogVideoX1.5 + "
        "EasyAnimate with a frozen Kinetics-400 VideoMAE-B/16; none of our generators is in its "
        "training set.")

    def __init__(self):
        from torchvision import transforms
        self.tf = transforms.Compose([
            transforms.Resize((224, 224), interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.ToTensor(),
            transforms.Normalize(mean=MEAN, std=STD),
        ])
        self.device = None

    # ------------------------------------------------------------------ CPU side
    def prepare(self, path):
        import av
        from PIL import Image
        with av.open(path) as c:
            frames = [fr for _, fr in zip(range(128), c.decode(c.streams.video[0]))]
        if len(frames) < 8:
            raise RuntimeError(f"only {len(frames)} frames")
        idx32 = np.linspace(0, len(frames) - 1, 32).astype(int)       # AIGVDBench extraction
        idx16 = np.linspace(0, 31, N_FRAMES, dtype=int)                 # V-PVP dataset.py
        out = torch.empty(N_FRAMES, 3, 224, 224)
        for k, j in enumerate(idx16):
            img = frames[idx32[j]].to_image()
            w, h = img.size
            m = min(w, h)
            left, top = (w - m) // 2, (h - m) // 2
            img = img.crop((left, top, left + m, top + m)).resize((256, 256), Image.BILINEAR)
            out[k] = self.tf(img)
        return out                                                       # (T, C, H, W)

    # ------------------------------------------------------------------ GPU side
    def load(self, device):
        for p, want in [(HEAD, HEAD_SHA), (os.path.join(BACKBONE, "model.safetensors"), BACKBONE_SHA)]:
            if sha256_file(p) != want:
                raise RuntimeError(f"checksum mismatch: {p}")
        if SRC not in sys.path:
            sys.path.insert(0, SRC)
        from backbones import BACKBONE_REGISTRY      # authors' code
        from pvp_head import PVPHead
        self.backbone = BACKBONE_REGISTRY["videomae_k400"](
            pretrained_model=BACKBONE, num_frames=N_FRAMES, img_size=224).to(device).eval()
        self.head = PVPHead("velocity_gated", D=768).to(device)
        self.head.load_state_dict(torch.load(HEAD, map_location="cpu", weights_only=True))
        self.head.eval()
        self.device = device
        return self

    @torch.no_grad()
    def score(self, batch):
        x = batch.to(self.device, non_blocking=True).float().permute(0, 2, 1, 3, 4)  # (B,C,T,H,W)
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            z = self.backbone.extract_patch_features(x)
        z = z.float()
        v = z[:, :, 1:, :] - z[:, :, :-1, :]
        return torch.sigmoid(self.head(z, v).double()).cpu()
