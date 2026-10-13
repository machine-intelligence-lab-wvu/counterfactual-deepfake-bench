"""Render a canonical prompt spec into a Wan 2.2 T2V prompt.

Deliberately the LTX 2.3 prompt minus its audio sentence (Wan 2.2 T2V is
video-only), so the generator is the only variable between the two matched runs.
The negative prompt is the LTX one for the same reason; note it is inert when
sampling with the 4-step lightx2v LoRA at cfg 1.0.

Known issue: on the 4-step path Wan renders small background figures in roughly
half of office/classroom scenes despite "nobody else visible". NAGuidance does
not patch Wan's attention in this ComfyUI, and a positive "the room behind is
deserted" clause was tested on 4 clips: it removed figures from one and added
them to another (2/4 -> 2/4) while lowering motion, so it was dropped. Handle
this in QC with a minimum-face-size gate rather than by diverging the prompt.
"""
import ltx23


def render(spec):
    """spec -> (positive, negative). Deterministic: same spec, same text."""
    positive, negative = ltx23.render(spec)
    positive = positive[:positive.rindex(" Audio: ")]
    return positive, negative
