"""Detector interface.

A detector turns one preprocessed view video into one score in [0, 1] (higher = more likely
generated). Work is split so decoding runs in DataLoader workers and only `score` touches the
GPU:

  prepare(path) -> tensor      CPU, called in worker processes, official preprocessing
  score(batch)  -> 1-D tensor  GPU, batch = stacked `prepare` outputs

Identity fields end up on every score row; `aggregate` refuses to mix rows whose
checkpoint_sha256 differs, and `run` re-scores a clip whenever detector_version changes.
"""
import abc


class Detector(abc.ABC):
    name: str = ""
    version: str = ""                 # adapter version; bump when preprocessing changes
    checkpoint_sha256: str = ""
    preprocess_spec: dict = {}        # official preprocessing applied on top of the view
    default_threshold: float = 0.5    # official decision rule, or 0.5 if none
    threshold_source: str = ""
    report_note: str = ""             # caveat printed in every REPORT.md for this detector
    implemented: bool = True

    @abc.abstractmethod
    def load(self, device):
        """Load weights onto `device`; verify checksums."""

    @abc.abstractmethod
    def prepare(self, path):
        """Decode and preprocess one video into the model input (CPU)."""

    @abc.abstractmethod
    def score(self, batch):
        """Return one score in [0, 1] per item of `batch`."""

    def identity(self):
        return {"detector": self.name, "detector_version": self.version,
                "checkpoint_sha256": self.checkpoint_sha256}


class NotImplementedDetector(Detector):
    """Placeholder so planned detectors show up in the registry and coverage."""
    implemented = False

    def load(self, device):
        raise NotImplementedError(f"{self.name}: adapter not implemented yet")

    def prepare(self, path):
        raise NotImplementedError

    def score(self, batch):
        raise NotImplementedError
