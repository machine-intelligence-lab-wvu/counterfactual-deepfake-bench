"""Detector registry. Adding a detector = one folder under eval/detectors/ + one line here."""
import importlib

REGISTRY = {
    "decof": "eval.detectors.decof.adapter:DeCoF",
    "demamba": "eval.detectors.demamba.adapter:DeMamba",
    "d3": "eval.detectors.d3.adapter:D3",
    "vpvp": "eval.detectors.vpvp.adapter:VPVP",
    "aigvdet": "eval.detectors.aigvdet.adapter:AIGVDet",          # stub
    "clip_probe": "eval.detectors.clip_probe.adapter:CLIPProbe",  # stub
    "altfreezing": "eval.detectors.altfreezing.adapter:AltFreezing",  # stub
}


def get(name):
    if name not in REGISTRY:
        raise SystemExit(f"unknown detector {name!r}; known: {sorted(REGISTRY)}")
    mod, cls = REGISTRY[name].split(":")
    return getattr(importlib.import_module(mod), cls)()


def implemented():
    out = []
    for n in REGISTRY:
        try:
            if get(n).implemented:
                out.append(n)
        except Exception:
            pass
    return out
