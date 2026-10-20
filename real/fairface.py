"""FairFace demographics for the real half, mapped onto the datagen taxonomy.

The checkpoint shipped in this project is named `fairface_alldata_4race_...pth`,
but the name is wrong: its head is `fc: (18, 512)` and the Drive id it was
fetched from is FairFace's `res34_fair_align_multi_7`. 18 logits = 7 race +
2 gender + 9 age, i.e. the SEVEN-race model, which is the one that matches
`specs/taxonomy.py`. Verified before use rather than trusted, because the 4-race
model has a 15-wide head and would silently mis-slice if it ever got swapped in.

Logit order follows FairFace's own predict.py: [:7] race, [7:9] gender,
[9:18] age.

As in the taxonomy's own docstring, these are *perceived* presentation labels
produced by a classifier, not self-identified identity. They carry FairFace's
documented error profile and should be reported as such.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms

# FairFace's native label order (predict.py), do not reorder.
RACE_LABELS = ["white", "black", "latino_hispanic", "east_asian",
               "southeast_asian", "indian", "middle_eastern"]
GENDER_LABELS = ["male", "female"]
AGE_LABELS = ["0-2", "3-9", "10-19", "20-29", "30-39",
              "40-49", "50-59", "60-69", "70+"]

# FairFace race -> taxonomy race key (specs/taxonomy.py RACES)
RACE_TO_CELL = {
    "white": "white",
    "black": "black",
    "latino_hispanic": "latino",
    "east_asian": "east_asian",
    "southeast_asian": "southeast_asian",
    "indian": "indian",
    "middle_eastern": "mena",
}

GENDER_TO_CELL = {"male": "m", "female": "f"}

# FairFace age band -> taxonomy age band.
#
# Two boundaries do not line up and are handled explicitly rather than rounded
# away:
#   - 0-2 / 3-9 / 10-19 are dropped. The taxonomy starts at 18-29, and 10-19
#     straddles the age of majority; no clip of a possible minor belongs in a
#     deepfake benchmark, so the whole band is excluded rather than split.
#   - 40-49 straddles the 44/45 cut between the taxonomy's 30-44 and 45-59.
#     It is kept but flagged `age_ambiguous`, carrying both candidate bands, so
#     it can be included or excluded at analysis time instead of being silently
#     forced into one cell.
AGE_TO_CELL = {
    "0-2": None, "3-9": None, "10-19": None,
    "20-29": "18-29",
    "30-39": "30-44",
    "40-49": "30-44",          # ambiguous, see AGE_AMBIGUOUS
    "50-59": "45-59",
    "60-69": "60+",
    "70+": "60+",
}
AGE_AMBIGUOUS = {"40-49": ("30-44", "45-59")}


class FairFace:
    def __init__(self, weights_path: str | Path, device: str = "cuda", batch_size: int = 32):
        self.device = torch.device(
            device if (device == "cpu" or torch.cuda.is_available()) else "cpu")
        self.batch_size = batch_size

        sd = torch.load(str(weights_path), map_location="cpu", weights_only=False)
        if hasattr(sd, "state_dict"):
            sd = sd.state_dict()
        out = sd["fc.weight"].shape[0]
        if out != 18:
            raise ValueError(
                f"{weights_path} has a {out}-wide head; this code assumes the "
                f"7-race FairFace model (18 = 7 race + 2 gender + 9 age). "
                f"A 15-wide head is the 4-race model and needs a different slice.")

        m = models.resnet34(weights=None)
        m.fc = nn.Linear(m.fc.in_features, 18)
        missing, unexpected = m.load_state_dict(sd, strict=False)
        if missing or unexpected:
            raise ValueError(f"checkpoint mismatch: missing={missing} unexpected={unexpected}")
        self.model = m.to(self.device).eval()

        self.tf = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])

    @torch.no_grad()
    def predict_batch(self, crops_bgr: list[np.ndarray]) -> list[dict]:
        """Per-crop probabilities. Crops are BGR, as OpenCV returns them."""
        out = []
        for i in range(0, len(crops_bgr), self.batch_size):
            chunk = crops_bgr[i:i + self.batch_size]
            t = torch.stack([self.tf(cv2.cvtColor(c, cv2.COLOR_BGR2RGB))
                             for c in chunk]).to(self.device)
            logits = self.model(t).float().cpu()
            for row in logits:
                out.append({
                    "race": torch.softmax(row[:7], 0).numpy(),
                    "gender": torch.softmax(row[7:9], 0).numpy(),
                    "age": torch.softmax(row[9:18], 0).numpy(),
                })
        return out

    def predict_clip(self, crops_bgr: list[np.ndarray]) -> dict:
        """Clip-level demographics by averaging probabilities over face crops.

        Averaging probabilities rather than majority-voting hard labels keeps the
        margin information: a clip the model is unsure about across every frame
        ends with a low confidence instead of a confident label manufactured by
        a 5-4 vote.
        """
        if not crops_bgr:
            return {"ok": False, "reason": "no face crops"}
        preds = self.predict_batch(crops_bgr)
        race = np.mean([p["race"] for p in preds], axis=0)
        gender = np.mean([p["gender"] for p in preds], axis=0)
        age = np.mean([p["age"] for p in preds], axis=0)

        ri, gi, ai = int(race.argmax()), int(gender.argmax()), int(age.argmax())
        race_lbl, gender_lbl, age_lbl = RACE_LABELS[ri], GENDER_LABELS[gi], AGE_LABELS[ai]
        cell_age = AGE_TO_CELL[age_lbl]

        res = {
            "ok": True,
            "n_crops": len(crops_bgr),
            "fairface_race": race_lbl,
            "fairface_race_conf": round(float(race[ri]), 3),
            "fairface_gender": gender_lbl,
            "fairface_gender_conf": round(float(gender[gi]), 3),
            "fairface_age": age_lbl,
            "fairface_age_conf": round(float(age[ai]), 3),
            "race": RACE_TO_CELL[race_lbl],
            "gender": GENDER_TO_CELL[gender_lbl],
            "age_band": cell_age,
            "age_ambiguous": int(age_lbl in AGE_AMBIGUOUS),
            "age_band_alt": AGE_AMBIGUOUS.get(age_lbl, (None, None))[1],
            # full distributions, so a later re-binning needs no re-inference
            "race_probs": {l: round(float(v), 4) for l, v in zip(RACE_LABELS, race)},
            "gender_probs": {l: round(float(v), 4) for l, v in zip(GENDER_LABELS, gender)},
            "age_probs": {l: round(float(v), 4) for l, v in zip(AGE_LABELS, age)},
        }
        res["cell"] = (f"{res['race']}__{res['gender']}__{cell_age}"
                       if cell_age else None)
        res["cell_excluded_reason"] = None if cell_age else f"age {age_lbl} below taxonomy floor"
        return res
