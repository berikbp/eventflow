"""Initialize the ignored local .env without displaying its organizer secret."""

import re
from pathlib import Path
from secrets import token_urlsafe

from app.core.config import ROOT


def initialize(root: Path = ROOT) -> bool:
    path = root / ".env"
    content = (
        path.read_text(encoding="utf-8-sig")
        if path.exists()
        else (root / ".env.example").read_text(encoding="utf-8-sig")
    )
    match = re.search(r"^ORGANIZER_TOKEN=(.*)$", content, flags=re.MULTILINE)
    if match and match.group(1).strip().strip("\"'"):
        return False
    line = "ORGANIZER_TOKEN=" + token_urlsafe(48)
    if match:
        content = content[: match.start()] + line + content[match.end() :]
    else:
        content = content.rstrip() + "\n" + line + "\n"
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


if __name__ == "__main__":
    changed = initialize()
    print(
        "Local .env initialized; open it to view ORGANIZER_TOKEN."
        if changed
        else "Existing ORGANIZER_TOKEN preserved."
    )
