import curses
from typing import Callable, List, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import ColorPalette, Drawable, GenStr, Hitbox, KeyCaptureDrawable


# ==== Drawable objects: props ====
class WrapperScrollableStackVertical(KeyCaptureDrawable):
    # TODO: add docstr

    def __init__(
        self,
        y: int,
        x: int,
        max_displayed_count: int,
        kcd_height: int,
        parent: Drawable | None = None,
        palette: Optional[ColorPalette] = ColorPalette(),
    ):
        """TODO: docstr"""
        super().__init__(y, x, parent)

        self.max_displayed_count = max_displayed_count
        self.kcd_height = kcd_height
        self._scroll = 0
        self._cursor = 0

        self._kcds: List[KeyCaptureDrawable] = []  # List of kcds inside
        self.palette = palette

        # self.kcd.capture_goto = (
        #     self._custom_kcd_capture_goto
        # )  # override the capture_goto method of the kcd

        self.capture_remove = self._capture_remove
        self.capture_take = self._capture_take

    def draw(self, window: cwin) -> None:
        y, x = self.get_yx()
        for kcd in self._kcds:
            kcd.y = y  # TODO: change
            kcd.x = x
            kcd.draw(window)
        # self.kcd.draw(window)
        # y, x = self.get_yx()

        # if self.state == 2:  # reset button selected
        #     Drawable.draw_str(GenStr(("\u27F2 ", self.palette.button_selected)), window, y, x)
        # else:  # reset button not selected
        #     Drawable.draw_str(GenStr((("\u27F2 ", self.palette.button_unselected))), window, y, x)

    def key_behaviour(self, key: int) -> None:
        pass
        # if self.state == 1:  # kcd selected
        #     self.kcd.key_behaviour(key)  # pass the key to the kcd
        # elif self.state == 2:  # reset selected
        #     if key == ord("\n"):
        #         try_self_call(self.kcd, self.reset_action)

        #     elif key == curses.KEY_RIGHT:
        #         self.state = 1  # select the kcd
        #         origin = self.get_yx()
        #         self.kcd.capture_take(origin, 1)

        #     elif key == curses.KEY_LEFT:
        #         self.state = 0
        #         if self.capture_goto:
        #             origin = self.get_hitbox().tl
        #             self.capture_goto(origin, 3)  # goto left

        #     elif key == curses.KEY_UP:
        #         origin = self.get_hitbox().tl
        #         self.capture_goto(origin, 2)  # goto up
        #     elif key == curses.KEY_DOWN:
        #         origin = self.get_hitbox().br  # goto down
        #         self.capture_goto(origin, 0)

    def add_kcd(self, kcd: KeyCaptureDrawable) -> None:
        self._kcds.append(kcd)

    def get_hitbox(self) -> Hitbox:
        if self._overwritten_hitbox:
            return self._hitbox
        else:
            y, x = self.get_yx()
            tl = (y, x)
            br = (y + self.kcd_height * self.max_displayed_count, x)
            return Hitbox(tl, br)

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
