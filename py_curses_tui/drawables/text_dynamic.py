"""
TextDynamic Drawable for dynamic text rendering.
"""

from typing import Optional, override, Callable

from ..core import Drawable
from ..genstr import GenStr
from ..utils.draw_utils import draw_genstr
from ..utils.colors import Palette


class TextDynamic(Drawable):
    """A simple text element."""

    @override
    def __init__(
        self,
        text_getter: Callable[["TextDynamic"], GenStr],
        y: int,
        x: int,
        width: Optional[int] = None,
        do_center: bool = False, # Does nothing if width is None.
        parent: Optional[Drawable] = None,
        palette: Optional[Palette] = None,
    ) -> None:
        """Dynamic text element, where the text is defined by the return value of a function.
        
        Palette:
            - primary: The default color pair for the text, for GenStr sections with no specified color."""
        super().__init__(y, x, parent, palette)
        self.text_getter = text_getter
        self.width = width
        self.do_center = do_center

    @override
    def draw(self, window) -> None:
        """Draw the text element."""
        super().draw(window)
        y, x = self.get_y_x()
        palette = self.get_palette()

        text_to_draw: GenStr = self.text_getter(self)  # Retrieve text
        if self.width is not None:
            if self.do_center:
                text_to_draw = text_to_draw.centered(self.width)
            else:
                text_to_draw = text_to_draw.padded(self.width)

        draw_genstr(window, y, x, text_to_draw, palette.primary)
