import curses
from curses import window as cwin
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Literal, Optional, override
from .utils.draw_utils import draw_genstr
from .genstr import GenStr
from enum import Enum

# =====================================
#  Base Classes
# =====================================


class RedrawSignal(Exception):
    """Exception to signal a redraw of the UI."""


class KeyBehaviourFlag(Enum):
    """Flag for key_behaviour."""

    SKIPPED = 0  # Key not used (e.g. no key behaviour)
    HANDLED = 1  # Key used (e.g. button press)
    EXIT = -1  # Ask to remove selection (e.g. navigate out)


class Drawable:
    """A drawable object."""

    def __init__(
        self,
        y: int,
        x: int,
        parent: Optional["Drawable"] = None,
    ):
        """A drawable object.

        Args:
            y (int): y-coordinate of the Drawable object.
            x (int): x-coordinate of the Drawable object.
            parent (Optional[Drawable]): Parent Drawable object for relative coordinates, such as a Menu or another Drawable. If None, the coordinates are absolute to the window.
        """
        self.y, self.x = y, x
        self.parent = parent
        self._first_draw = True  # Whether the drawable has been drawn at least once, used to trigger first draw behaviour.

    def _get_y_x(self) -> tuple[int, int]:
        """Get the absolute y and x coordinates of the drawable object, taking into account the parent drawables."""
        if self.parent is None:
            return (self.y, self.x)
        parent_y, parent_x = self.parent._get_y_x()
        return (self.y + parent_y, self.x + parent_x)

    @abstractmethod
    def draw(self, window: cwin) -> None:
        """Draw the object.

        Args:
            window (curses.window): Window to draw on.
        """
        if self._first_draw:
            self._on_first_draw()

    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected.

        Args:
            y_prev (int): y-value of the previously selected Drawable.
            x_prev (int): x-value of the previously selected Drawable.

        Return (bool):
            Whether the Drawable can be captured.
        """
        return False  # Non-capturing drawable.

    def key_behaviour(self, key: int) -> KeyBehaviourFlag:
        """Behaviour of the Drawable in reponse to a key input.

        Args:
            - key (int): key to process

        Return (KeyBehaviourFlag):
            Flag to communicate how the key was handled.
        """
        # Non-capturing drawables by default.
        raise NotImplementedError(
            "Non-capturing Drawable should never receive key input."
        )

    def _on_first_draw(self) -> None:
        """Behaviour to execute on the first draw of the drawable object."""
        if self._first_draw:
            self._first_draw = False


class Submenu(Drawable):
    """Elementary unit for drawable navigation, draws and control drawables it contains."""

    @override
    def __init__(self, auto_select_capturable_drawable_on_first_draw: Literal[None, "First", "Last"] = None):
        """A submenu spanning all the window."""
        super().__init__(0, 0)
        self.drawables: list[Drawable] = []
        self._selected_drawable_index: int = 0
        self._auto_select_capturable_drawable_on_first_draw = auto_select_capturable_drawable_on_first_draw

    def select_drawable(self, index: int) -> None:
        """Select a drawable by index. This is the expected way to define the selected drawable on application start."""
        self._selected_drawable_index = index
        self._check_selected_drawable()

    def get_selected_drawable_index(self) -> int:
        """Get the index of the currently selected drawable.

        Return (int):
            Index of the currently selected drawable.
        """
        self._check_selected_drawable()
        return self._selected_drawable_index
    
    @override
    def _on_first_draw(self) -> None:
        if self._auto_select_capturable_drawable_on_first_draw == "First":
            y, x = self._get_y_x()
            for i, drawable in enumerate(self.drawables):
                if drawable.capture(y, x):
                    self.select_drawable(i)
                    break
        elif self._auto_select_capturable_drawable_on_first_draw == "Last":
            y, x = self._get_y_x()
            for i in range(len(self.drawables) - 1, -1, -1):
                if self.drawables[i].capture(y, x):
                    self.select_drawable(i)
                    break

        return super()._on_first_draw()

    @override
    def draw(self, window: cwin) -> None:
        """Draw the menu and its drawables."""
        if self._first_draw:
            self._on_first_draw()

        for drawable in self.drawables:
            drawable.draw(window)

    @override
    def capture(self, y_prev: int, x_prev: int) -> bool:
        """Whether the Drawable can be selected."""
        y, x = self._get_y_x()
        if not self.drawables:  # If no drawable, cannot be captured.
            return False

        # TODO: via score / distance
        # TODO: for now, temp behaviour
        # Capture the last drawable if coming from the right or below.
        if x_prev > x or (x_prev == x and y_prev > y):
            self.select_drawable(len(self.drawables) - 1)
        else:  # Capture the first drawable if coming from the left or above, or if there are no drawables.
            self.select_drawable(0)

        return True  # Accept capture.

    @override
    def key_behaviour(self, key: int) -> KeyBehaviourFlag:
        """Behaviour of the Submenu in reponse to a key input.

        Args:
            - key (int): key to process

        Return (KeyBehaviourFlag):
            Flag to communicate how the key was handled.
        """
        if not self.drawables:
            return KeyBehaviourFlag.SKIPPED  # Nothing to do since there is no drawable.

        # Check selected drawable validity.
        self._check_selected_drawable()
        selected_drawable = self.drawables[self._selected_drawable_index]

        # Call selected drawable's key_behaviour
        flag = selected_drawable.key_behaviour(key)

        if flag is KeyBehaviourFlag.SKIPPED:
            return (
                KeyBehaviourFlag.SKIPPED
            )  # Key not captured by selected drawable, skip.
        elif flag is KeyBehaviourFlag.HANDLED:
            return KeyBehaviourFlag.HANDLED  # Key handled by selected drawable, exit.
        elif flag is KeyBehaviourFlag.EXIT:
            # Drawable wishes not to be captured anymore.
            # TODO: use score / distance
            # TODO: for now, temp behaviour
            # Find next capturing drawable.
            if key == curses.KEY_DOWN:
                # Go through the drawables until we find a capture-able one, or loop back to the start.
                prev_y, prev_x = selected_drawable._get_y_x()
                for i in range(self._selected_drawable_index + 1, len(self.drawables)):
                    if self.drawables[i].capture(prev_y, prev_x):
                        self.select_drawable(i)
                        return (
                            KeyBehaviourFlag.HANDLED
                        )  # Found a capture-able drawable, select it and exit.
                # Else no drawable found, try to remove capture
                return KeyBehaviourFlag.EXIT

            elif key == curses.KEY_UP:
                # Go through the drawables until we find a capture-able one, or loop back to the end.
                prev_y, prev_x = selected_drawable._get_y_x()
                for i in range(self._selected_drawable_index - 1, -1, -1):
                    if self.drawables[i].capture(prev_y, prev_x):
                        self.select_drawable(i)
                        return (
                            KeyBehaviourFlag.HANDLED
                        )  # Found a capture-able drawable, select it and exit.
                # Else no drawable found, try to remove capture
                return KeyBehaviourFlag.EXIT

        # else, nothing done
        return KeyBehaviourFlag.SKIPPED

    # @override
    # def _on_first_draw(self) -> None:
    #     super()._on_first_draw()

    def add_drawable(self, drawable: Drawable) -> int:
        """Add a drawable to the menu.

        Args:
            drawable (Drawable): Drawable to add.

        Return (int):
            Index of the added drawable in self.drawables."""
        self.drawables.append(drawable)
        return len(self.drawables) - 1

    def _check_selected_drawable(self) -> None:
        """Check whether the selected drawable index is valid."""
        if self._selected_drawable_index < 0 or self._selected_drawable_index >= len(
            self.drawables
        ):
            raise ValueError("Selected drawable index out of range.")


class Menu(Submenu):
    """A submenu spanning all the window."""

    @override
    def draw(self, window: cwin) -> None:
        """Draw the menu and its drawables."""
        # TODO: Draw the menu background

        super().draw(window)


class App:
    """Wrapper for the curses window, handles the main loop and user inputs."""

    def __init__(self, menus: list[Menu] = []) -> None:
        """Wrapper for the curses window, handles the main loop and user inputs."""
        self.menus = menus
        self.selected_menu: int = 0
        self._running = False

    def draw(self, window: cwin) -> None:
        """Draw the UI."""
        self._check_selected_menu()

        self.menus[self.selected_menu].draw(window)
        # TODO: Add floating menus

    def key_behaviour(self, key: int) -> None:
        """Handle key input."""
        self._check_selected_menu()

        if key == ord("q"):
            self._running = False  # Exit on 'q' key.
            return

        self.menus[self.selected_menu].key_behaviour(key)

    def _on_loop_start(self) -> None:
        """Behaviour to execute on the first draw of the UI."""
        self._check_selected_menu()

    def _check_selected_menu(self) -> None:
        """Check if the selected menu index is valid."""
        if self.selected_menu < 0 or self.selected_menu >= len(self.menus):
            if len(self.menus) == 0:
                raise ValueError("No menus to draw.")
            raise ValueError("Selected menu index out of range.")

    def _loop(self, window: cwin) -> None:
        """Main loop of the UI."""
        self._on_loop_start()

        self._running = True
        while self._running:
            try:
                self.draw(window)
                key = window.getch()
                self.key_behaviour(key)
            except KeyboardInterrupt:
                self._running = False  # Exit

    def start(self) -> None:
        """Main loop of the UI."""
        self._on_loop_start()

        curses.wrapper(self._loop)


# =====================================
#  Other
# =====================================

# class MenuFloating(Menu):
#     """Floating Menu object."""

#     def __init__(
#         self, y: int, x: int, h: int, w: int, default_selected: int | None = None
#     ):
#         """Floating menu object."""
#         super().__init__(default_selected)
#         self.y = y
#         self.x = x


# class MenuFloatingCentered(MenuFloating):
#     """Centered floating Menu object."""

#     def __init__(self, h: int, w: int, default_selected: int | None = None):
#         y, x = ...
#         super().__init__(y, x, h, w, default_selected)
