"""AltFreezing adapter (stub, not run yet).

TODO:
  - Checkpoint: official AltFreezing release (face-forgery specialist); record SHA256 and license.
  - Expects face crops: use the face512 view, then the authors' alignment/crop on top.
  - Score: authors' fake probability; threshold = their decision rule or 0.5.
"""
from eval.detectors.base import NotImplementedDetector


class AltFreezing(NotImplementedDetector):
    name = "altfreezing"
    version = "0"
