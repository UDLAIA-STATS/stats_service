import base64
from pathlib import Path

def image_to_base64(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    with open(p, "rb") as img:
        return base64.b64encode(img.read()).decode("utf-8")
