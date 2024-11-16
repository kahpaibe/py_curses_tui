import curses
from typing import Any, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import Drawable

MAX_PAIRS = 255  # TODO: for some reason, it seems like curses.COLOR_PAIRS's max pair is too high


# ==== Drawable objects: props ====
class RGBPreview(Drawable):
    """A box to display the specified color to RGB."""

    def __init__(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        color_index: int = -1,
        pair_index: int = -1,
        parent: Optional[Drawable] = None,
    ):
        """A box to display the specified color to RGB.

        Note: will overwrite the specified color_index's color and the specified by pair_index pair, so it is recommended to use the default value -1 and -1 (corresponding to maximum index values) while the user should avoid using high index values directly.
        This index is shared globally for the user interface, multiple RGBPreview objects will overwrite each other's color. Please specify a different index for each RGBPreview object if you want to use multiple RGBPreview objects.

        Args:
            y (int): y coordinate
            x (int): x coordinate
            height (int): height of the box
            width (int): width of the box
            color_index (int, optional): color index to overwrite. Defaults to -1 (meaning max).
            pair_index (int, optional): color pair index to overwrite. Defaults to -1 (meaning max).
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).

        Color palette:
            Unused

        on_update:
            Called when:
                rgb_preview.set_color_1000() is called.
                rgb_preview.set_color_255() is called.
                rgb_preview.set_color_hex() is called.
            Supressed before first draw.

        """
        super().__init__(y, x, parent)
        self.height, self.width = height, width
        self._color_index = color_index if color_index >= 0 else curses.COLORS - 1
        self._pair_index = pair_index if pair_index >= 0 else MAX_PAIRS
        curses.init_color(self._color_index, 1000, 0, 0)
        curses.init_pair(self._pair_index, self._color_index, self._color_index)

        self._first_draw = False  # whether it was drawn once. Sort of init

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        y, x = self.get_yx()
        Drawable.fill(window, y, x, y + self.height - 1, x + self.width - 1, self._pair_index)

    def set_color_1000(self, color: Tuple[int, int, int]) -> None:
        """Set the color of the box, by overwriting the color pair index.

        Uses curses' 1000 scale for RGB values."""
        curses.init_color(self._color_index, color[0], color[1], color[2])

        if self._first_draw:
            if self.on_update:
                try_self_call(self, self.on_update)

    def set_color_255(self, color: Tuple[int, int, int]) -> None:
        """Set the color of the box, by overwriting the color pair index.

        Uses the standard 24bit (0-255, 0-255, 0-255) scale for RGB values."""
        color = tuple(int(1000 * c / 255) for c in color)
        self.set_color_1000(color)

    def set_color_hex(self, hex_color: str) -> None:
        """Set the color of the box, by overwriting the color pair index.

        Uses HEX color code."""
        self.set_color_255(self.hex_to_rgb(hex_color))

    def get_color(self) -> Tuple[int, int, int]:
        """Get the color of the box, according to the color pair index color.

        Returns:
            Tuple[int, int, int]: RGB color code (0-255, 0-255, 0-255 scale).
        """
        r, g, b = curses.color_content(self._color_index)
        return (
            int(round(r / 1000 * 255)),
            int(round(g / 1000 * 255)),
            int(round(b / 1000 * 255)),
        )

    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert a HEX color to RGB (0-255, 0-255, 0-255 scale). No alpha channel.

        Args:
            hex_color (str): HEX color code. Example: "#34eb43" or "34eb43" or "0x34eb43".
        """
        hex_color = hex_color.lstrip("#")
        if hex_color.startswith("0x"):
            hex_color = hex_color[2:]
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb_color: Tuple[int, int, int]) -> str:
        """Convert an RGB color to HEX.

        Args:
            rgb_color (Tuple[int, int, int]): RGB color code (0-255, 0-255, 0-255 scale). Example: (52, 235, 67).
        """
        return f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"

    @staticmethod
    def validate_rgb(rgb_input: str) -> Tuple[str, Any]:
        """Validate if the RGB color code is correct. Returns its format and its formatted content as 255 format in a 2-uple.

        Available outputs:
            "invalid" : invalid format
            "255" : (int, int, int) of 0-255 scale
            # disabled # "1000" : (int, int, int) of 0-1000 scale
            "FFFFFF" : HEX color code
            "#FFFFFF" : HEX color code
            "0xFFFFFF" : HEX color code

        Args:
            rgb_input (str): RGB color code. Example: "52, 235, 67".
        """
        if "," in rgb_input:  # case 1 : "int, int, int" format
            try:
                r, g, b = rgb_input.split(",")
            except Exception:
                return ("invalid", None)
            if all(0 <= int(c) <= 255 for c in (r, g, b)):
                return ("255", (int(r), int(g), int(b)))
        elif ":" in rgb_input:
            try:
                r, g, b = rgb_input.split(":")
            except Exception:
                return ("invalid", None)
            if all(0 <= int(c) <= 255 for c in (r, g, b)):
                return ("255", (int(r), int(g), int(b)))

        elif len(rgb_input) == 6 and all(
            c in "0123456789ABCDEF" for c in rgb_input.upper()
        ):  # case 3 : "FFFFFF" format
            return ("FFFFFF", RGBPreview.hex_to_rgb(rgb_input))

        elif (
            len(rgb_input) == 7
            and rgb_input.startswith("#")
            and all(c in "0123456789ABCDEF" for c in rgb_input[1:].upper())
        ):  # case 4: "#FFFFFF" format
            return ("#FFFFFF", RGBPreview.hex_to_rgb(rgb_input))

        elif (
            len(rgb_input) == 8
            and rgb_input.startswith("0x")
            and all(c in "0123456789ABCDEF" for c in rgb_input[2:].upper())
        ):  # case 5: 0x123456 format
            return ("0xFFFFFF", RGBPreview.hex_to_rgb(rgb_input))

        return ("invalid", None)
