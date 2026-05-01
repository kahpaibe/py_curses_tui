"""
Text Drawable.
"""

from typing import Optional, override

from ..core import Drawable
from ..genstr import GenStr
from ..utils.draw_utils import draw_genstr
from ..utils.colors import Palette


class Text(Drawable):
    """A simple text element."""

    @override
    def __init__(
        self,
        text: GenStr,
        y: int,
        x: int,
        parent: Drawable | None = None,
        palette: Optional[Palette] = None,
    ) -> None:
        """A simple text element.
        
        Palette:
            - primary: The default color pair for the text, for GenStr sections with no specified color."""
        super().__init__(y, x, parent, palette)
        self.text = text

    @override
    def draw(self, window) -> None:
        """Draw the text element."""
        super().draw(window)
        y, x = self._get_y_x()
        palette = self.get_palette()

        draw_genstr(window, y, x, self.text, palette.primary)
