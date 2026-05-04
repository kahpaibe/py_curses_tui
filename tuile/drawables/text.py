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
        width: Optional[int] = None,
        do_center: bool = False, # Does nothing if width is None.
        parent: Optional[Drawable] = None,
        palette: Optional[Palette] = None,
    ) -> None:
        """A simple text element.
        
        Palette:
            - primary: The default color pair for the text, for GenStr sections with no specified color."""
        super().__init__(y, x, parent, palette)
        self.text = text
        self.width = width
        self.do_center = do_center

    @override
    def draw(self, window) -> None:
        """Draw the text element."""
        super().draw(window)
        y, x = self.get_y_x()
        palette = self.get_palette()

        text_to_draw: GenStr = self.text # Default: base text
        if self.width is not None:
            if self.do_center:
                text_to_draw = text_to_draw.centered(self.width)
            else:
                text_to_draw = text_to_draw.padded(self.width)

        draw_genstr(window, y, x, text_to_draw, palette.primary)
