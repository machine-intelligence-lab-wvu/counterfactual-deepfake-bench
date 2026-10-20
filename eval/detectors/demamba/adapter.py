"""DeMamba adapter (stub, not run yet).

TODO:
  - Checkpoint: official DeMamba release (GenVideo authors); record SHA256 and license.
  - Preprocessing: the authors' frame count, sampling, resolution and normalization, on top of the view.
  - Score: authors' fake-class probability; threshold = their decision rule or 0.5.
"""
from eval.detectors.base import NotImplementedDetector


class DeMamba(NotImplementedDetector):
    name = "demamba"
    version = "0"
