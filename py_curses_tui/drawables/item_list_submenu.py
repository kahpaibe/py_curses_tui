from typing import Any, Callable, List, Optional

from ..utility import try_self_call, cwin
from .base_classes import ColorPalette, Drawable, Submenu
from .button import Button
from .textinput import TextInput


class ItemListSubmenu(Submenu):
    """A list of items made of textinputs, buttons to remove such items and a button to add an item.

    Caution: this is a Submenu. It should be used in a menu directly, and should not contain external drawables.
    """

    # TODO: add max number of items ? or perhaps scrollable ?
    # To make it scrollable, might need to make it a KeyCaptureDrawable with navigation set manually and behaviour set manually

    add_symbol = "Add"
    remove_symbol = "x"

    def __init__(
        self,
        y: int,
        x: int,
        width: int,
        items: Optional[List[str]] = [],
        max_items: int = 10,  # max number of items
        parent: Optional[Drawable] = None,
        palette: Optional[ColorPalette] = None,
    ):
        """A list of items made of textinputs, buttons to remove such items and a button to add an item.

        Caution: this is a Submenu. It should be used in a menu directly, and should not contain external drawables.

        Args:
            y: y position.
            x: x position.
            width: width of this submenu.
            max_items: max number of items. 0: no limit. Defaults to 10.
            items: list of items to be displayed. Defaults to [].
            parent: optional parent drawable.
            palette: color palette. Defaults to None.

        Color palette:
            button_selected: color of the button when selected.
            button_unselected: color of the button when unselected.
            textinput_selected: color of the textinput when selected.
            textinput_unselected: color of the textinput when unselected.

        On update:
            Called when:
                - item_list_submenu.add_item() is called
                - item_list_submenu.remove_item() is called
                - item_list_submenu.clear_items() is called
                - item_list.set_items() is called
                - any text_input gets modified
            Suppressed before first draw.
        Warning: setting on_update should be done through the set_on_update method as it needs to the the callable for its child items.
        Accessing item_list_submenu.on_update directly should be avoided

        """
        self._first_draw = False  # whether it was drawn once. Sort of init
        self._palette = None
        super().__init__()
        self.y = y
        self.x = x
        self.width = width
        self.max_items = max_items
        self._dummy_parent = Drawable(y, x, parent, self._get_palette_bypass())  # parent for inside items
        self._text_inputs: List[TextInput] = []
        self._remove_buttons: List[Button] = []

        self._add_button = Button(
            "Add", 0, 0, self._add_press, self._dummy_parent, self._get_palette_bypass(), width, centered=True
        )

        self.on_update: Callable[[Submenu], Any] | None = None
        self._build(items)

        self._first_draw = False  # whether it was drawn once. Sort of init
        self.set_palette(palette, False) # None if not set, should be overwritten when adding to a container

    def _add_press(self, a: Any = None) -> None:
        self.add_item()

    def draw(self, window: cwin) -> None:
        if not self._first_draw:
            self._first_draw = True
        return super().draw(window)

    def add_item(self, value: str = "") -> None:
        """Add an item to the list."""
        i = len(self._text_inputs)
        y = len(self._text_inputs)
        x = 0
        text_input_width = self.width - 1 - len(self.remove_symbol)
        text_input = TextInput(y, x, text_input_width, 0, self._dummy_parent, self._get_palette_bypass())
        text_input.set_text(value)

        def remove(selfo: Any, index: int = i) -> None:
            self.remove_item(index)

        remove_button = Button(
            self.remove_symbol,
            y,
            x + text_input_width + 1,
            remove,
            self._dummy_parent,
            self._get_palette_bypass(),
            len(self.remove_symbol),
            centered=True,
        )

        text_input.on_update = self.on_update

        # add to the submenu
        self.add(text_input)
        self.add(remove_button)
        self._add_button.y = y + 1

        self._text_inputs.append(text_input)
        self._remove_buttons.append(remove_button)

        if self.max_items > 0 and len(self._text_inputs) >= self.max_items:
            self._kcds.pop(0)  # remove add button

        self.activate(i * 2 + 1)  # activate this item

        if self._first_draw:  # suppress before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def remove_item(self, index: int) -> None:
        """Remove item at given index from the list, 0 being the 0th text input."""
        self._text_inputs.pop(index)
        self._remove_buttons.pop(index)

        # rebuild
        items = self.get_items()
        self._build(items)

        if index < len(self._text_inputs):
            self.activate(index * 2 + 2)  # activate next item's remove button
        else:
            self.activate(index * 2)

        if self._first_draw:  # suppress before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def clear_items(self) -> None:
        """Remove all items from the list."""
        self._text_inputs.clear()
        self._remove_buttons.clear()
        self._build([])

        self.activate(0)  # activate add button

        if self._first_draw:  # suppress before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def _build(self, items: List[str]) -> None:
        """Build the submenu with is kcds."""
        NOT_SELECTED = True if self.get_selected_index() < 0 else False

        self.clear()
        self._text_inputs.clear()
        self._remove_buttons.clear()
        self._add_button.y = 0
        if self.max_items > 0 and len(items) < self.max_items:
            self.add(self._add_button)
        for item in items:
            self.add_item(item)
        if NOT_SELECTED:
            self.activate(-1)  # disable if was disabled

    def get_items(self) -> List[str]:
        """Return the list of items."""
        return [ti.get_text() for ti in self._text_inputs]

    def set_items(self, items: List[str]) -> None:
        """Set the list of items."""
        self._build(items)

        if self._first_draw:  # suppress before first draw
            if self.on_update:
                try_self_call(self, self.on_update)

    def set_on_update(
        self, on_update: Callable[[Drawable], Any] | None = None, exclude: List[Drawable] = []
    ) -> None:  # override
        """The right way to set on_update to a item_list_submenu object."""
        self.on_update = on_update
        for ti in self._text_inputs:
            ti.on_update = on_update
        self._add_button.on_update = on_update

    def set_palette(self, palette, should_override = False) -> None:
        super().set_palette(palette, should_override)
        for ti in self._text_inputs:
            ti.set_palette(palette, should_override)