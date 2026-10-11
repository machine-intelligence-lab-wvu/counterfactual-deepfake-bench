"""Render a canonical prompt spec into an LTX 2.3 prompt.

LTX 2.3's own prompting guidance (bundled template) asks for three things:
  1. core actions as they occur over time
  2. explicit visual detail
  3. audio - sounds and dialogue
so the renderer emits an Action / Visual / Audio-shaped dense prose prompt.

The negative prompt carries the fix for the P0 finding that office scenes render
faint background figures, which would trip the "exactly one face" QC gate and
produce scene-correlated rejection rates.
"""

NEGATIVE = (
    "multiple people, crowd, background people, extra faces, second person, "
    "reflection of a person, poster of a face, deformed face, distorted facial "
    "features, asymmetric eyes, extra fingers, malformed hands, text, caption, "
    "subtitles, watermark, logo, cartoon, anime, illustration, painting, "
    "3d render, cgi, plastic waxy skin, oversaturated, overexposed, "
    "low quality, blurry, "
    # stillness terms carry weight here - 3 of the first 12 samples came out
    # effectively frozen, so this is not decorative
    "static frozen image, still photograph, motionless, rigid face, "
    "frozen expression, unmoving head, slideshow, single held pose"
)
# Deliberately NOT here: pillarbox / letterbox / "black bars" terms. Adding them
# (and a positive "no black bars" clause) was tested and made pillarboxing
# markedly WORSE - 411-739 dark columns versus 328-336 with this prompt. Naming
# an artifact appears to inject it, since negation is unreliable through the text
# encoder. Pillarboxing has to be handled by content choice or post-processing.


def render(spec):
    """spec -> (positive, negative). Deterministic: same spec, same text."""
    d = spec["demographic"]
    a = spec["appearance"]
    s = spec["scene"]
    c = spec["camera"]
    b = spec["action"]
    pron = "She" if d["gender_word"] == "woman" else "He"

    positive = (
        # --- subject + demographic (the controlled variable)
        # NOTE: dropping "documentary" here was tested and made pillarboxing
        # WORSE (542-739 dark columns vs 328-336), so it stays.
        f"Photorealistic documentary video portrait of "
        f"{d.get('article', 'a')} {d['race_phrase']} "
        f"{d['gender_word']} {d['age_phrase']}, {d['age_detail']}, "
        f"with {a['hair']}, wearing {a['attire']}. "
        # --- core action over time (LTX tip 1)
        # The closing motion clause is load-bearing: without it LTX renders some
        # behaviours as an almost still image (interframe motion < 0.25).
        f"{pron} is {b['behavior']}. "
        f"Continuous natural movement throughout the entire shot, with repeated "
        f"eye blinks, shifting gaze and small involuntary head motion; "
        f"the face is never still. "
        # --- visual detail (LTX tip 2)
        f"Background: {s['setting']}. Lighting: {s['lighting']}. "
        f"{c['framing']}. "
        f"Single person alone in the frame, nobody else visible, "
        f"sharp natural focus on the face, realistic skin texture with pores "
        f"and fine detail, natural colour, shot on a full-frame camera. "
        # --- audio (LTX tip 3)
        f"Audio: {b['audio']}."
    )
    return positive, NEGATIVE
