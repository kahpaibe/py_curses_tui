import curses
from typing import List, Optional

from ..utility import cwin, try_self_call
from .base_classes import AttrStr, Drawable, GenStr, ColorPalette


# ==== Drawable objects: props ====
class Text(Drawable):
    """A text that can be drawn."""

    def __init__(
        self,
        text: GenStr | str,
        y: int,
        x: int,
        color_pair_id: int | None = None,
        parent: Optional[Drawable] = None,
        width: Optional[int] = 0,
        centered: Optional[bool] = False,
        attributes: List[int] = [curses.A_NORMAL],
    ):
        """A text that can be drawn.

        Args:
            text (GenStr | str): text to draw. Can be a GenStr object or a string.
            y (int): y coordinate
            x (int): x coordinate
            color_pair_id (int, optional): color pair index. Defaults to None = default palette text.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).
            width (int, optional): width of the text (if centered=True)
            centered (bool, optional): whether the text should be centered. Defaults to False. If True, width should be given.
            attributes (List[int], optional): list of attributes. e.g., [curses.A_BOLD, curses.A_ITALIC].

        Color palette:
            Unused: color of the text is defined by the given color_pair_id.

        on_update:
            Called when:
                text.set_text() is called.
            Supressed before first draw.

        About GenStr:
            GenStr is a list of AttrStr objects. It is used to store text with different attributes.
            Each AttrStr object has the following attributes:
                text: str
                color_pair_id: int
                attributes: List[int]
        """
        super().__init__(y, x, parent)
        self.color_pair_id = color_pair_id
        self.attributes = attributes

        self._width = width
        self._centered = centered
        self._text: GenStr = GenStr()

        self._first_draw = False  # whether it was drawn once. Sort of init
        self.set_text(text)

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()
        Drawable.draw_str(self._text, window, y, x, self.attributes, self.color_pair_id)

    def get_text(self) -> str:  # alias
        """Return the text as a string."""
        return self._text.unfolded()

    def set_text(self, text: GenStr | AttrStr | str) -> None:
        """Set the text.

        Args:
            text (GenStr | str): text to draw. Can be a GenStr object or a string.
        """
        if isinstance(text, str):
            self._text = GenStr(AttrStr(text, self.color_pair_id, self.attributes))
        elif isinstance(text, GenStr):
            self._text = text
        elif isinstance(text, AttrStr):
            self._text = GenStr([text])

        else:
            raise TypeError(
                f"text must be a GenStr object, a AttrStr object or a string, not {type(text)}"
            )

        # if centered, recalculate the text
        if self._centered:
            self._text = Drawable.get_genstr_fixed_size(GenStr(text), self._width, True)

        if self._first_draw:  # supressed before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def set_palette(self, palette: ColorPalette, should_override = True):
        """Set the color palette. For the Text object, will override the text color."""
        if should_override:
            self.color_pair_id = palette.text
        if self.color_pair_id is None: # Use default palette color if not set
            self.color_pair_id = palette.text