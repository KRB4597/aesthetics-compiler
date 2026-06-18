from enum import Enum


class CompilerTier(str, Enum):
    RULE = "rule"
    IMAGE = "image"
    HTML = "html"
    MULTIMEDIA = "multimedia"
    LLM = "llm"
    MOCK = "mock"


class InputMode(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    HTML = "html"
    MULTIMEDIA = "multimedia"


ALL_PROJECTIONS = ["birkhoff", "arnheim", "berlyne", "gestalt"]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".gif"}
HTML_EXTENSIONS = {".html", ".htm"}
MULTIMEDIA_EXTENSIONS = {".mp4", ".avi", ".mov", ".webm", ".mkv", ".gif"}
TEXT_EXTENSIONS = {".txt", ".md", ""}


def detect_input_mode(path: str) -> InputMode:
    import pathlib
    suffix = pathlib.Path(path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return InputMode.IMAGE
    if suffix in HTML_EXTENSIONS:
        return InputMode.HTML
    if suffix in MULTIMEDIA_EXTENSIONS:
        return InputMode.MULTIMEDIA
    return InputMode.TEXT
