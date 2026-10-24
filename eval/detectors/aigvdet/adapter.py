"""AIGVDet adapter (stub, not run yet).

TODO:
  - Checkpoint: official AIGVDet release (RGB and optical-flow branches); record SHA256 and license.
  - Optical flow: pin the flow model (RAFT) and its weights; flow is computed on the view frames.
  - Score: authors' fusion of the two branches; threshold = their decision rule or 0.5.
"""
from eval.detectors.base import NotImplementedDetector


class AIGVDet(NotImplementedDetector):
    name = "aigvdet"
    version = "0"
