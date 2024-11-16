from typing import Optional

from ..utility import cwin
from .base_classes import ColorPalette, Drawable, DrawableContainer


# ==== Drawable objects: props ====
class Box(DrawableContainer):
    """A box that can be drawn."""

    def __init__(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        palette: Optional[ColorPalette] = ColorPalette(),
        parent: Optional[Drawable] = None,
    ):
        """A box that can be drawn.

        Args:
            y (int): y coordinate
            x (int): x coordinate
            height (int): height of the box
            width (int): width of the box
            palette (ColorPalette, optional): color palette. Defaults to ColorPalette().
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).

        Color palette:
            box: color of the background and borders

        on_update:
            Never called.
        """
        super().__init__(y, x, parent)
        self.palette = palette
        self.height, self.width = height, width

    def draw(self, window: cwin) -> None:
        y, x = self.get_yx()
        Drawable.fill(window, y, x, y + self.height - 1, x + self.width - 1, self.palette.box)
        Drawable.rectangle(
            window, (y, x), (y + self.height - 1, x + self.width - 1), self.palette.box
        )
        super().draw(window)  # draw every child inside the box
