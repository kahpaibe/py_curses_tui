import curses
from typing import Callable, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import ColorPalette, Drawable, GenStr, Hitbox, KeyCaptureDrawable


# ==== Drawable objects: props ====
class WrapperReset(KeyCaptureDrawable):
    """A wrapper kcd to add a reset button to a kcd."""

    def __init__(
        self,
        kcd: KeyCaptureDrawable,
        reset_action: Callable[[KeyCaptureDrawable | None], None],
        merge_hitbox: bool = False,
        relative_position: Tuple[int, int] = (0, -2),
        palette: Optional[ColorPalette] = None,
    ):
        """A wrapper kcd to add a reset button to a kcd.

        Args:
            kcd (KeyCaptureDrawable): The kcd to wrap.
            reset_action (Callable[[KeyCaptureDrawable | None], None]): The action to perform when the reset button is pressed.
            merge_hitbox (bool, optional): Whether the hitboxes of the kcd and the reset button should be merged (False means using the kcd's hitbox directly). Defaults to False.
            relative_position (Tuple[y:int, x:int], optional): The relative position of the reset button to the kcd. Defaults to (0, -2).
            palette (Optional[ColorPalette], optional): The color palette to use. Defaults to None.

        ColorPalette:
            button_selected: The color of the reset button when selected.
            button_unselected: The color of the reset button when not selected.

        Note:
            reset_action may have 0 arguments, or 1 argument reset_action(kcd) where kcd is the kcd object.

        Example usage:
            dropdown = Dropdown(0,0, ui, ["Car","Plane", "Train"])
            dropdown_with_reset = WrapperReset(dropdown, lambda kcd: kcd.set_option("Car"))
            menu.add_key_capture_drawable(dropdown_with_reset, 0)
        """
        y, x = relative_position
        self.kcd = kcd
        super().__init__(y, x, kcd)

        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container
        # self.kcd.x += 2  # Move the kcd to the right
        self.reset_action = reset_action
        self.merge_hitbox = merge_hitbox  # if hitboxes should be merged

        self.state = 0  # 0: not selected, 1: kcd selected, 2: reset selected

        self.kcd.capture_goto = (
            self._custom_kcd_capture_goto
        )  # override the capture_goto method of the kcd

        self.capture_remove = self._capture_remove
        self.capture_take = self._capture_take

    def draw(self, window: cwin) -> None:
        self.kcd.draw(window)
        y, x = self.get_yx()

        if self.state == 2:  # reset button selected
            Drawable.draw_str(GenStr(("\u27F2 ", self._get_palette_bypass().button_selected)), window, y, x)
        else:  # reset button not selected
            Drawable.draw_str(GenStr((("\u27F2 ", self._get_palette_bypass().button_unselected))), window, y, x)

    def key_behaviour(self, key: int) -> None:
        if self.state == 1:  # kcd selected
            self.kcd.key_behaviour(key)  # pass the key to the kcd
        elif self.state == 2:  # reset selected
            if key == ord("\n"):
                try_self_call(self.kcd, self.reset_action)

            elif key == curses.KEY_RIGHT:
                self.state = 1  # select the kcd
                origin = self.get_yx()
                self.kcd.capture_take(origin, 1)

            elif key == curses.KEY_LEFT:
                self.state = 0
                if self.capture_goto:
                    origin = self.get_hitbox().tl
                    self.capture_goto(origin, 3)  # goto left

            elif key == curses.KEY_UP:
                origin = self.get_hitbox().tl
                self.capture_goto(origin, 2)  # goto up
            elif key == curses.KEY_DOWN:
                origin = self.get_hitbox().br  # goto down
                self.capture_goto(origin, 0)

    def get_hitbox(self) -> Hitbox:
        if self._overwritten_hitbox:
            return self._hitbox
        elif self.merge_hitbox:
            kcd_hitbox = self.kcd.get_hitbox()
            y, x = self.get_yx()
            tl = (min(y, kcd_hitbox.tl[0]), min(x, kcd_hitbox.tl[1]))
            br = (max(y, kcd_hitbox.br[0]), max(x, kcd_hitbox.br[1]))
            return Hitbox(tl, br)  # merged hitbox
        else:
            return self.kcd.get_hitbox()  # kcd's hitbox

    def _capture_remove(self, direction: int) -> None:
        """Remove the capture.
        direction 0: down, 1: right, 2: up, 3: left"""
        if self.state == 1:
            self.kcd.capture_remove(direction)
        self.state = 0

    def _capture_take(self, origin: Tuple[int, int], direction: int) -> None:
        """Takeover the capture.
        origin = (y,x), coordinates of the origin cursor"""
        self.kcd.capture_take(origin, direction)
        self.state = 1

    def _custom_kcd_capture_goto(self, origin: Tuple[int, int], direction: int) -> None:
        """Overrides the capture_goto method of the kcd to be able to go from the kcd to the reset button."""

        if direction == 3:  # if from kcd going left
            self.state = 2  # select the reset button
            self.kcd.capture_remove(3)
        else:
            self.capture_goto(origin, direction)

    def set_palette(self, palette, should_override = False) -> None:
        super().set_palette(palette, should_override)
        self.kcd.set_palette(palette, should_override)
    
    def get_palette(self) -> ColorPalette:
        return self.kcd.get_palette()
