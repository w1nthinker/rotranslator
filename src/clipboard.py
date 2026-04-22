from __future__ import annotations

import pyperclip


def copy_json(text: str) -> bool:
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException:
        return False
    return True
