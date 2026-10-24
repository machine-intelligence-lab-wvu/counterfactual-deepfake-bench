"""Kandinsky 6.0 Pro renderer: the LTX 2.3 prompt, unchanged.

K6 generates synchronized audio like LTX, so the prompt keeps its " Audio: ..." sentence (Wan,
which has no audio, drops it). The negative prompt is ours, as for every generator, not K6's
built-in default.
"""
from ltx23 import render, NEGATIVE  # noqa: F401
