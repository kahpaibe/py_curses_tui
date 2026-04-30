"""
Text Drawable.
"""

from ..core import Drawable
from ..genstr import GenStr
from typing import override
from ..utils.draw_utils import draw_genstr

class Text(Drawable):
    """A simple text element."""

    @override
    def __init__(self, text: GenStr, y: int, x: int, parent: Drawable | None = None):
        """A simple text element."""
        super().__init__(y, x, parent)
        self.text = text

    @override
    def draw(self, window) -> None:
        """Draw the text element."""
        super().draw(window)
        y, x = self._get_y_x()
        draw_genstr(window, y, x, self.text)