"""
Filled box (no capture).
"""

from typing import Optional, override

from ..core import Drawable
from ..utils.draw_utils import draw_rectangle
from ..utils.colors import Palette


class Box(Drawable):
    """A simple filled box element."""

    @override
    def __init__(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        parent: Optional[Drawable] = None,
        palette: Optional[Palette] = None,
    ) -> None:
        """A simple filled box element.

        Palette:
            - primary: The default color pair for the box (background and border)."""
        super().__init__(y, x, parent, palette)
        self.height = height
        self.width = width

    @override
    def draw(self, window) -> None:
        """Draw the box."""
        y, x = self.get_y_x()
        palette = self.palette if self.palette else Palette(0, 0, 0)


        draw_rectangle(window, y, x, self.height, self.width, palette.primary)
        