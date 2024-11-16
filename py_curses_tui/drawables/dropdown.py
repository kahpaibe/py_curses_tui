from dataclasses import replace
from typing import TYPE_CHECKING, Callable, List, Optional

from .base_classes import ColorPalette, Drawable, cwin
from .button import Button

if TYPE_CHECKING:  # allow type checking for UserInterface
    from ..core import UserInterface


class DropDown(Button):
    """A dropdown menu to select a string value from a list of strings."""

    def __init__(
        self,
        y: int,
        x: int,
        ui: "UserInterface",
        options: List[str] = [],
        allow_invalid_option: bool = False,
        width_override: Optional[int] = None,
        parent: Drawable | None = None,
        palette: Optional[ColorPalette] = ColorPalette(),
    ):
        """A dropdown menu to select a string value from a list of strings.

        Args:
            y (int): y coordinate
            x (int): x coordinate
            ui (UserInterface): UserInterface object
            options (List[str], optional): list of options. Defaults to [].
            allow_invalid_option (bool, optional): whether to allow invalid options. Defaults to False.
            width_override (Optional[int], optional): overrides the width. Defaults to None.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).
            palette (ColorPalette, optional): color palette. Defaults to ColorPalette().

        Color palette:
            button_selected: color of the button when selected.
            button_unselected: color of the button when unselected.

        On update:
            Called when:
                dropdown.set_option() is called.
                dropdown.set_options() is called.
                dropdown.set_text() is called.
        Suppressed before first draw

        Note:
            The dropdown's first option should be manually set to the desired value using set_option().
        """
        self._width_override = width_override
        self.allow_invalid_option = allow_invalid_option
        self.palette: ColorPalette = replace(palette)  # copy

        self.button_selected_col = self.palette.button_selected
        self.button_unselected_col = self.palette.button_unselected
        self.button_selected_invalid_col = self.palette.button_selected_invalid
        self.button_unselected_invalid_col = self.palette.button_unselected_invalid
        super().__init__("", y, x, self._action, parent, self.palette, width=1, centered=False)
        self._ui = ui
        self._options: List[str] = []
        self.set_options(options)

        if len(self._options) > 0:
            self.set_text(self._options[0])

    def _action(self, selfobj: Optional[Drawable] = None) -> None:
        """Makes the drop down (pop up menu)"""
        actions: List[Callable] = []
        for i in range(len(self._options)):

            def action(selfobj: Optional[Drawable] = None, option: str = self._options[i]) -> None:
                self.set_option(option)

            actions.append((self._options[i], action))
        self._ui.pop_up("Please select an option", actions, "OPTION")

    def clear(self) -> None:
        """Clear all options"""
        self._options.clear()

        if self._first_draw:
            if self.on_update:
                self.on_update()

    def add_option(self, option: str) -> None:
        """Add an option to the list."""
        self._options.append(option)
        # make all options of length the max length
        if self._width_override:
            max_len = self._width_override
        elif len(self._options) > 0:
            max_len = max(len(option) for option in self._options)
        else:
            max_len = 0
        self._Button_width = max_len  # set width accordingly

        if len(option) < max_len:
            self._options[-1] = option.ljust(max_len)
        elif len(option) > max_len:
            for i in range(len(self._options)):
                self._options[i] = self._options[i].ljust(len(option))

        if self._first_draw:
            if self.on_update:
                self.on_update()

    def set_options(self, options: List[str]) -> None:
        """Set the options."""
        self._options = options
        if len(self._options) > 0:
            if self._width_override:
                max_len = self._width_override
            else:
                max_len = max(len(option) for option in self._options)
            for i in range(len(self._options)):
                self._options[i] = self._options[i].ljust(max_len)
            self.set_text(self._options[0])
            self._width = max_len  # set width accordingly

        if self._first_draw:
            if self.on_update:
                self.on_update()

    def get_option(self) -> str:
        """Get the selected option string."""
        return self.get_text().strip()

    def set_option(self, option: str) -> None:
        """Set the selected option."""
        o = option.strip()
        if not self.is_valid_option(o):
            if not self.allow_invalid_option:
                raise ValueError(f"Option {o.__repr__()} not in options {self._options}")
            else:
                self.palette.button_selected = self.button_selected_invalid_col
                self.palette.button_unselected = self.button_unselected_invalid_col
        else:
            self.palette.button_selected = self.button_selected_col
            self.palette.button_unselected = self.button_unselected_col
        max_len = max(len(op) for op in self._options)
        self.set_text(option.ljust(max_len))

        if self._first_draw:
            if self.on_update:
                self.on_update()

    def is_valid_option(self, option: str) -> bool:
        """Returns whether the option is a valid option."""
        return option.strip() in map(str.strip, self._options)

    def draw(self, win: cwin) -> None:
        """Draw the dropdown."""
        super().draw(win)
