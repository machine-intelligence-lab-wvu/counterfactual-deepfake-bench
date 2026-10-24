"""DeepFake Bench: demographic taxonomy and confound-balancing banks.

Taxonomy is FairFace-compatible (7 race x 2 gender x 4 age = 56 cells) so that
FairFace/MiVOLO classifiers can gate generation output in QC, and so results are
comparable with prior per-subgroup detector studies.

These videos encode *perceived* demographic presentation, not self-identified
identity - synthetic people have no self-identification. Say so in the paper.
"""

# ---------------------------------------------------------------- demographics

RACES = [
    ("white",        "White"),
    ("black",        "Black"),
    ("east_asian",   "East Asian"),
    ("southeast_asian", "Southeast Asian"),
    ("indian",       "South Asian"),
    ("mena",         "Middle Eastern"),
    ("latino",       "Hispanic"),
]

GENDERS = [("m", "man", "his"), ("f", "woman", "her")]

# Age phrasing is deliberately heavy-handed for the older bands: plan section 5.4
# documents that video models under-comply with age prompts and skew young.
# Post-hoc verification still gates these - the prompt is not trusted.
# age_detail carries SKIN and STRUCTURE only - never hair colour. Hair colour is
# owned by the age-tiered HAIR bank below, otherwise the two contradict each
# other ("grey hair ... with wavy black hair") and the model gets a self-
# conflicting prompt.
AGE_BANDS = [
    ("18-29", ["in {poss} early twenties", "in {poss} mid twenties",
               "in {poss} late twenties"],
     "smooth youthful skin, no wrinkles", "young"),
    ("30-44", ["in {poss} early thirties", "in {poss} late thirties",
               "in {poss} early forties"],
     "faint expression lines, healthy adult skin", "young"),
    ("45-59", ["in {poss} late forties", "in {poss} early fifties",
               "in {poss} mid fifties"],
     "visible fine lines around the eyes and mouth, middle-aged features", "mid"),
    ("60+",   ["in {poss} late sixties", "in {poss} seventies",
               "in {poss} late seventies"],
     "clearly elderly, deeply wrinkled and creased skin, age spots, "
     "sagging jawline, hooded eyelids, thinning skin", "old"),
]

# Hair is tiered by age so colour agrees with the age band. Style stays constant
# within a race/gender so the demographic cell reads consistently.
HAIR = {
    "white": {
        "m": {"young": ["short brown hair", "cropped blond hair"],
              "mid":   ["short brown hair greying at the temples", "greying cropped hair"],
              "old":   ["thin grey hair", "white hair, receding at the temples"]},
        "f": {"young": ["shoulder-length blonde hair", "wavy brown hair"],
              "mid":   ["shoulder-length brown hair with grey streaks", "greying wavy hair"],
              "old":   ["short white hair", "soft grey hair"]}},
    "black": {
        "m": {"young": ["closely cropped black hair", "a short afro"],
              "mid":   ["closely cropped hair greying at the temples", "a greying short afro"],
              "old":   ["closely cropped grey hair", "a short white afro"]},
        "f": {"young": ["natural afro hair", "long braided black hair"],
              "mid":   ["a greying natural afro", "braided hair with grey strands"],
              "old":   ["short grey coiled hair", "a white natural afro"]}},
    "east_asian": {
        "m": {"young": ["short straight black hair", "neatly parted black hair"],
              "mid":   ["short black hair greying at the temples", "salt-and-pepper hair"],
              "old":   ["thin grey hair", "short white hair"]},
        "f": {"young": ["shoulder-length straight black hair", "long black hair"],
              "mid":   ["shoulder-length black hair with grey strands", "greying straight hair"],
              "old":   ["short grey hair", "white hair tied back"]}},
    "southeast_asian": {
        "m": {"young": ["short straight black hair", "tousled dark hair"],
              "mid":   ["short dark hair greying at the temples", "salt-and-pepper hair"],
              "old":   ["thin grey hair", "short white hair"]},
        "f": {"young": ["long straight dark hair", "shoulder-length dark hair"],
              "mid":   ["dark hair with grey strands", "greying shoulder-length hair"],
              "old":   ["grey hair tied back", "short white hair"]}},
    "indian": {
        "m": {"young": ["short thick black hair", "neatly combed dark hair"],
              "mid":   ["thick black hair greying at the temples", "salt-and-pepper hair"],
              "old":   ["thin grey hair", "short white hair"]},
        "f": {"young": ["long dark hair tied back", "shoulder-length wavy black hair"],
              "mid":   ["dark hair with grey streaks, tied back", "greying wavy hair"],
              "old":   ["grey hair tied back", "short white hair"]}},
    "mena": {
        "m": {"young": ["short dark hair with a trimmed beard", "short black hair"],
              "mid":   ["short dark hair with a greying beard", "salt-and-pepper hair"],
              "old":   ["thin grey hair with a white beard", "short white hair"]},
        "f": {"young": ["long dark wavy hair", "shoulder-length dark brown hair"],
              "mid":   ["dark wavy hair with grey strands", "greying shoulder-length hair"],
              "old":   ["grey hair", "short white hair"]}},
    "latino": {
        "m": {"young": ["short dark brown hair", "wavy black hair"],
              "mid":   ["dark hair greying at the temples", "salt-and-pepper wavy hair"],
              "old":   ["thin grey hair", "short white hair"]},
        "f": {"young": ["long wavy dark brown hair", "shoulder-length black hair"],
              "mid":   ["dark wavy hair with grey streaks", "greying shoulder-length hair"],
              "old":   ["grey hair", "short white hair"]}},
}


def article(word):
    """'a' / 'an' agreement - 'a East Asian' reads as a typo in a released prompt."""
    return "an" if word[:1].lower() in "aeiou" else "a"

# ------------------------------------------------- confound-balancing banks
# Rule (plan 5.3): nothing here may be culturally or socioeconomically marked,
# and every bank entry must be assignable to every demographic cell.

SETTINGS = [
    ("office",     "a modern open-plan office, softly blurred behind the subject"),
    ("plainwall",  "a plain neutral grey wall directly behind the subject"),
    ("livingroom", "a simple living room with a sofa softly blurred behind"),
    ("library",    "a quiet library with blurred shelves behind the subject"),
    ("cafe",       "a small cafe interior, softly blurred behind the subject"),
    ("corridor",   "a plain indoor corridor, softly blurred behind"),
    ("studio",     "a plain seamless studio backdrop"),
    ("kitchen",    "a tidy domestic kitchen, softly blurred behind"),
    ("classroom",  "an empty classroom, softly blurred behind the subject"),
    ("lobby",      "a quiet building lobby, softly blurred behind"),
]

# Includes the low-light / backlit / harsh conditions plan 5.3 requires be spread
# uniformly across race cells - lighting x skin-tone is a known detector-bias axis.
LIGHTING = [
    ("softwindow", "soft natural light from a window to one side"),
    ("overcast",   "flat even overcast daylight"),
    ("warmlamp",   "warm indoor lamplight from above"),
    ("harsh",      "harsh direct overhead lighting casting hard shadows"),
    ("backlit",    "strong backlight from a window behind, face in shadow with rim light"),
    ("lowlight",   "dim low-key indoor lighting, deep shadows"),
]

# Each behaviour is written as an explicit sequence of events over time, which is
# what LTX 2.3's prompting guide asks for. The earlier phrasings were states
# rather than sequences ("smiling and nodding slowly") and produced near-frozen
# clips - interframe motion 0.09-0.24 versus 2.4-4.2 for the talking behaviours.
# Every entry must name at least two distinct movements that resolve in order.
BEHAVIORS = [
    ("speak",   "talking continuously to the camera, mouth opening and closing on "
                "every word, eyebrows rising and falling with emphasis, head "
                "shifting slightly with each phrase",
                "a calm neutral voice speaking quietly"),
    # 'smile' remained the weakest behaviour after the first motion fix - still
    # 27% frozen inside group 14 - so it now opens with head movement rather
    # than an expression change, which LTX animates far more reliably.
    ("smile",   "first turning the head slightly and raising the eyebrows, then "
                "breaking into a wide smile as the cheeks lift and the eyes "
                "crease, nodding twice with clear visible head movement, then "
                "tilting the head to one side",
                "quiet room tone"),
    ("listen",  "nodding twice, then tilting the head to one side as the eyebrows "
                "lift, blinking slowly, then straightening up with a small smile",
                "quiet room tone"),
    ("turn",    "turning the head steadily to one side, pausing briefly, then "
                "turning back to face the camera as the hair shifts with the "
                "movement",
                "quiet room tone"),
    ("laugh",   "laughing out loud with the shoulders shaking and the head tipping "
                "back, then settling forward into a broad smile",
                "a soft quiet laugh"),
    ("read",    "reading aloud continuously, lips and jaw moving on every syllable, "
                "eyes tracking left to right across the line, blinking between lines",
                "a steady quiet reading voice"),
    ("think",   "looking up and away as the brow furrows, holding the thought, then "
                "turning back to the camera and raising the eyebrows",
                "quiet room tone"),
    ("pause",   "taking a visible breath so the shoulders rise and fall, glancing "
                "down and then back up at the camera, then breaking into a brief smile",
                "quiet room tone"),
]

ATTIRE = [
    "a plain casual shirt", "a plain knit sweater", "a simple t-shirt",
    "a plain button-down shirt", "a plain blouse", "a plain zip-up jacket",
]

CAMERA = [
    ("static",   "static camera, head-and-shoulders portrait framing, face centred"),
    ("slowsway", "near-static handheld camera with a slight natural sway, "
                 "head-and-shoulders portrait framing, face centred"),
]

# LTX 2.3 snaps height to a multiple of 32, so 704 (not 720) is its real output.
# Wan and Hunyuan both accept 704 at no extra cost -> use 704 everywhere for
# exact cross-generator resolution parity.
RESOLUTION = (1280, 704)

# 24 fps, LTX temporal latent stride 8 -> length must be 8k+1.
# 121 -> 5.04 s, 145 -> 6.04 s  (the approved 5-6 s window)
LTX_LENGTHS = [121, 145]
LTX_FPS = 24


def cells():
    """All 56 intersectional cells as (race_key, gender_key, age_band)."""
    return [(r[0], g[0], a[0]) for r in RACES for g in GENDERS for a in AGE_BANDS]


def cell_id(race, gender, age):
    return f"{race}__{gender}__{age}"
