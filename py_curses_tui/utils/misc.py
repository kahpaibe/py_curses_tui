"""
Other miscellaneous utilities.
"""

def centered_text(text: str, width: int) -> str:
    """Returns the given text centered within the given width. If the text is wider than the width, it will be truncated."""
    if len(text) >= width:
        return text[:width]
    padding = (width - len(text)) // 2
    return " " * padding + text + " " * (width - len(text) - padding)
