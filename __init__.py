"""Muse Fish S2 Prompter - free community nodes by Muse Collective (fish_prompter.py, whisper_transcribe.py)."""
from .fish_prompter import NODE_CLASS_MAPPINGS as _P, NODE_DISPLAY_NAME_MAPPINGS as _PN
from .whisper_transcribe import NODE_CLASS_MAPPINGS as _W, NODE_DISPLAY_NAME_MAPPINGS as _WN   # [2026-11-16]

NODE_CLASS_MAPPINGS = {**_P, **_W}
NODE_DISPLAY_NAME_MAPPINGS = {**_PN, **_WN}
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
