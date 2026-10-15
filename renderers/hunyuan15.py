"""Render a canonical prompt spec into a HunyuanVideo 1.5 T2V prompt.

Same text as the Wan 2.2 run: the LTX 2.3 prompt minus its audio sentence
(Hunyuan 1.5 T2V is video-only), with the LTX negative prompt. Unlike Wan's
4-step path, the negative is active here (cfg 6.0).
"""
import wan22


def render(spec):
    """spec -> (positive, negative). Deterministic: same spec, same text."""
    return wan22.render(spec)
