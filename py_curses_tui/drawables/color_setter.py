import curses
from typing import TYPE_CHECKING, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import (
    ColorPalette,
    Drawable,
)
from .button import Button
from .rgb_preview import MAX_PAIRS, RGBPreview

if TYPE_CHECKING:
    from ..core import UserInterface


# ==== Drawable objects: props ====
class ColorSetter(Button):
    """A basic object to set a color and preview it."""

    def __init__(
        self,
        y: int,
        x: int,
        ui: "UserInterface",
        default_color: Tuple[int, int, int] = (255, 0, 0),
        pair_id: int = -1,
        color_id: int = -1,
        color_format: str = "FFFFFF",
        parent: Drawable | None = None,
        palette: Optional[ColorPalette] = None,
    ):
        """A basic object to set a color and preview it.

        Args:
            y (int): y position of the object.
            x (int): x position of the object.
            ui (UserInterface): the UserInterface object.
            default_color (Tuple[int, int, int], optional): The default color to display. Defaults to (255, 0, 0).
            pair_id (int, optional): The pair id to use. Defaults to -1 (maximum id).
            color_id (int, optional): The color id to use. Defaults to -1 (maximum id).
            color_format (str, optional): The format to display the color in. Defaults to "255, 255, 255".
            parent (Drawable | None, optional): The parent object. Defaults to None.
            palette (Optional[ColorPalette], optional): The color palette to use. Defaults to None.

        About color_format: change displayed color format. Supported formats:
            255, 255, 255
            255 255 255
            255:255:255
            FFFFFF
            #FFFFFF
            0xFFFFFF

        Color palette:
            button_selected: color of the button when selected.
            button_unselected: color of the button when unselected.

        On update:
            Called when:
                color_setter.set_text() is called.
                color_setter.set_color() is called.
        Suppressed before first draw.
        """
        if color_format in [
            "255, 255, 255",
            "255:255:255",
            "255 255 255",
            "FFFFFF",
            "#FFFFFF",
            "0xFFFFFF",
        ]:
            self.color_format = color_format
        else:
            raise ValueError(f"Invalid color format: {color_format}")
        self.pair_id = pair_id if pair_id >= 0 else MAX_PAIRS - 1
        self.color_id = color_id if color_id >= 0 else curses.COLORS - 1
        self.ui = ui

        self.rgb_preview = RGBPreview(y, x + 14, 1, 2, color_id, pair_id, parent)

        self._first_draw = False  # whether it was drawn once. Sort of init

        def prompt_color(selfbutton: Button = None):
            def confirm_action(selftext: str):
                # raise ValueError(f"{selftextinput=}, {selftextinput.get_text()=}")
                color = selftext
                f, color = self.rgb_preview.validate_rgb(color)
                if f != "invalid":
                    self.set_color(color)
                    if self.on_update:
                        try_self_call(self, self.on_update)
                else:
                    ui.warning(f"Invalid color format for\n{color}")

            ui.prompt(
                "Enter the color in RGB format\n\ne.g. 255, 255, 255",
                "COLOR INPUT",
                20,
                confirm_action,
                default_value=self.get_color(),
            )

        self.rgb_preview.set_color_255(default_color)

        super().__init__( # Button.__init__
            self._format(default_color, color_format),
            y,
            x,
            prompt_color,
            parent,
            palette,
            13,
            False,
        )

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        super().draw(window)
        self.rgb_preview.draw(window)

    @staticmethod
    def _format(color: Tuple[int, int, int], color_format: str) -> str:
        if color_format == "255, 255, 255":
            return f"{color[0]}, {color[1]}, {color[2]}"
        elif color_format == "255 255 255":
            return f"{color[0]} {color[1]} {color[2]}"
        elif color_format == "255:255:255":
            return f"{color[0]}:{color[1]}:{color[2]}"
        elif color_format == "FFFFFF":
            return f"{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        elif color_format == "#FFFFFF":
            return f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        elif color_format == "0xFFFFFF":
            return f"0x{color[0]:02X}{color[1]:02X}{color[2]:02X}"
        else:
            raise ValueError(f"Invalid color format: {color_format}")

    def set_color(self, color: Tuple[int, int, int]) -> None:
        """Set the color of the object as (0-255, 0-255, 0-255) format"""
        self.rgb_preview.set_color_255(color)
        self.set_text(self._format(color, self.color_format))

    def get_color(self) -> Tuple[int, int, int]:
        color = self.rgb_preview.get_color()
        return self._format(color, self.color_format)