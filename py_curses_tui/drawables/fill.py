from typing import Optional

from ..utility import cwin
from .base_classes import ColorPalette, Drawable, DrawableContainer


# ==== Drawable objects: props ====
class Fill(DrawableContainer):
    """A box without borders, just fills the area"""

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
            color_pair_id (int, optional): color pair index of background and borders. Defaults to 0 = default terminal color pair.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).

        Color palette:
            box: fill color.
        """
        super().__init__(y, x, parent)
        self.palette = palette
        self.height, self.width = height, width

    def draw(self, window: cwin) -> None:
        y, x = self.get_yx()
        Drawable.fill(window, y, x, y + self.height - 1, x + self.width - 1, self.palette.box)
        super().draw(window)  # draw every child inside the box
