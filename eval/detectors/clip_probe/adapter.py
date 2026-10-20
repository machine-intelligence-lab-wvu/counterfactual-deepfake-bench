"""CLIPProbe adapter (stub, not run yet).

TODO:
  - Frozen CLIP features with a linear probe (UnivFD-style); decide the training data for the
    probe (must not include our clips) and record it.
  - Frame sampling and pooling to a video-level score in [0, 1].
"""
from eval.detectors.base import NotImplementedDetector


class CLIPProbe(NotImplementedDetector):
    name = "clip_probe"
    version = "0"
