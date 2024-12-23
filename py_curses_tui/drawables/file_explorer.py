import curses
import os
import pathlib
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple

from ..utility import cwin, try_self_call
from .base_classes import (
    Choice,
    ColorPalette,
    Drawable,
    GenStr,
)
from .scrollable_choose import ScrollableChoose
from .text import Text

if TYPE_CHECKING:
    from ..core import UserInterface


def list_volumes() -> List[str]:
    """Return a list of all available volumes (Windows only)."""
    if os.name != "nt":  # if not on windows
        raise OSError("This function is only available on Windows.")

    import ctypes

    drives: List[str] = []  # get list of drives
    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for letter in range(26):
        if bitmask & (1 << letter):
            drives.append(chr(65 + letter) + ":\\")
    return drives


# ==== Drawable objects: props ====
class FileExplorer(ScrollableChoose):
    """A simple file explorer widget."""

    directory_symbol = "d "  # displayed : f"{directory_symbol} {directoryname}"
    file_symbol = "f "  # displayed : f"{file_symbol} {filename}"
    volume_symbol = "D "  # displayed : f"{volume_symbol} {volumename}"

    def __init__(
        self,
        y: int,
        x: int,
        height: int,
        width: int,
        dir_mode: bool = False,
        default_path: Optional[str | pathlib.Path] = pathlib.Path.home(),
        file_or_dot_action: Callable[[str], Any] = None,
        ui: Optional["UserInterface"] = None,
        filter_: Optional[List[str]] = [],
        show_dim_files: bool = True,
        palette: Optional[ColorPalette] = None,
        parent: Drawable | None = None,
    ):
        """A simple file explorer widget.

        Args:
            y (int): y coordinate
            x (int): x coordinate
            height (int): height of the box
            width (int): width of the box
            dir_mode (bool, optional): if True, only directories are shown and allows selecting directories. Defaults to False.
            default_path (str | pathlib.Path, optional): default path to start from. Defaults to pathlib.Path.home() home directory.
            file_or_dot_action (Callable[[str], Any], optional): action to execute on file or directory selection. The argument is the path of the selected file or directory. Defaults to None.
            ui (UserInterface, optional): UserInterface object. Defaults to None.
            filter_ (List[str], optional): list of file extensions to allow. filter_ = [] disables filtering. Defaults to [].
            show_dim_files (bool, optional): if True and dir_mode = True, files will be shown with dim color even in directory mode. Defaults to True.
            palette (ColorPalette, optional): color palette. Defaults to None.
            parent (Drawable, optional): parent in hierarchy (e.g. may be used for relative coordinates).

        Color palette:
            file_explorer_file: file in file explorer
            file_explorer_directory: directory in file explorer
            file_explorer_dots: dot directories (current / parent) in file explorer
            file_explorer_dim: dimmed text for file or directory in file explorer
            file_explorer_selected: selected file or directory name preview in file explorer
            file_explorer_path: path in file explorer
            file_explorer_scrollbar: scrollbar in file explorer
        If called from ui.browse_file or ui.browse_directory, explorer_prompt_ variants are used instead.

        on_update:
            Called when:
                Changing directory. (self._goto_directory() is called)
            Supressed before first draw.

        The file_or_dot_action action may be provided with a str argument.
        Example:
            file_or_dot_action = lambda s: print(f'You selected the file {s} !') # where s in the path of the selected file or directory.
        """

        if height < 3:
            raise ValueError("height must be at least 3")
        if width < 5:
            raise ValueError("width must be at least 5")
        if len(filter_) > 0 and dir_mode:
            raise NotImplementedError("No filtering is supported for dir_mode=True")

        self._dummy_parent = Drawable(
            0, 0, parent
        )  # dummy parent to have working relative coordinates
        self._selected_text = Text(
            "", y + height, x, 0, self._dummy_parent # Color id set later by self.set_palette()
        )
        self._path_text = Text("", y, x, 0, self._dummy_parent) # Color id set later by self.set_palette()
        super().__init__(y + 1, x, 1, [], palette, 1, self._dummy_parent)
        self._width, self._height = width, height - 1  # limit the width of the texts
        self._ui = ui
        self.filter_ = [f.lower() for f in filter_]

        self._show_dim_files = show_dim_files
        if dir_mode:  # dir_mode: only directorys
            self._hide_files = True
            self._hide_directories = False
            self._show_current_directory = True
        else:
            self._hide_files = False  # hide files
            self._hide_directories = False
            self._show_current_directory = False

        self._file_or_dot_action: Callable[[int], Any] = file_or_dot_action

        self._path = pathlib.Path(default_path).resolve()  # default to home

        self._set_path_text_value(str(self._path))
        self._items: List[str] = []  # list of items in the current directory
        self._build_choices()
        self.update_selected_text()

        self._first_draw = False  # to suppress on_update before first draw
        self.capture_take = self._capture_take
        self.capture_remove = self._capture_remove

    def add_choice(self, choice: Choice, item_str: str = "") -> None:  # override
        """Add a choice to the list of choices.

        Overrride of ScrollableChoose.add_choice to add items (files/directories) to the list of items.

        if item_str is not provided, the choice text is used as item_str.
        """
        if len(item_str) == 0:
            self._items.append(GenStr.unfold(choice.text))
        else:
            self._items.append(item_str)
        super().add_choice(choice)

    def clear_choices(self) -> None:  # override
        """Clear the list of choices and items.

        Overrride of ScrollableChoose.add_choice to clear items (files/directories) from the list of items.
        """
        self._items.clear()
        super().clear_choices()

    def get_items(self) -> List[str]:
        """Return the list of items (files/directories) in the current directory."""
        return self._items

    def _build_choices(self) -> None:
        """List files and directories in the current directory."""
        self.clear_choices()
        gsdd = GenStr((f"{self.directory_symbol}..", self._get_palette_bypass().file_explorer_dots))
        self.add_choice(Choice(gsdd, self._go_up))
        if self._show_current_directory:

            def dot_action(index: int) -> None:
                self._file_or_dot_action(str(self._path))  # call for cwd

            gsd = GenStr(
                (
                    f"{self.directory_symbol}" + "{select current directory}",
                    self._get_palette_bypass().file_explorer_dots,
                )
            )
            self.add_choice(Choice(gsd, dot_action))
        files: List[str] = []
        directories: List[str] = []
        for item in self._path.iterdir():  # item categories
            if item.is_dir():
                directories.append(item.name)
            elif item.is_file():
                if len(self.filter_) == 0 or item.suffix.lower() in self.filter_:
                    files.append(item.name)
            else:
                pass  # should not happen

        if not self._hide_directories:  # directories first, files next
            for directory in sorted(directories):
                t = GenStr(
                    (self.directory_symbol, self._get_palette_bypass().file_explorer_directory),
                    (
                        directory[: self._width - len(self.directory_symbol)],
                        self._get_palette_bypass().file_explorer_directory,
                    ),
                )
                self.add_choice(Choice(t, self._goto_directory), directory)
        if not self._hide_files:
            for file in sorted(files):
                t = GenStr(
                    (self.file_symbol, self._get_palette_bypass().file_explorer_file),
                    (
                        file[: self._width - len(self.file_symbol)],
                        self._get_palette_bypass().file_explorer_file,
                    ),
                )

                def file_action(path: pathlib.Path = self._path / file) -> None:
                    if self._file_or_dot_action:
                        self._file_or_dot_action(str(path))  # call with file path

                self.add_choice(Choice(t, file_action), file)
        else:
            if self._show_dim_files:  # dim files
                for file in sorted(files):
                    t = GenStr(
                        (self.file_symbol, self._get_palette_bypass().file_explorer_dim),
                        (
                            file[: self._width - len(self.file_symbol)],
                            self._get_palette_bypass().file_explorer_dim,
                        ),
                    )
                    self.add_choice(Choice(t, None), file)

    def _build_choices_volumes(self) -> None:
        """Show all drives, available on Windows only."""
        if os.name != "nt":
            raise OSError("This function is only available on Windows.")
        self.clear_choices()
        drives = list_volumes()
        for drive in drives:
            t = GenStr(
                (self.volume_symbol, self._get_palette_bypass().file_explorer_directory),
                (
                    drive[: self._width - len(self.volume_symbol)],
                    self._get_palette_bypass().file_explorer_directory,
                ),
            )

            def drive_action(path: str = drive) -> None:
                self._path = pathlib.Path(path)
                self._set_path_text_value(str(self._path))
                self._build_choices()
                self.set_choice(0)

            self.add_choice(Choice(t, drive_action), drive)

    def draw(self, window: cwin) -> None:
        if self._first_draw:
            self._first_draw = False
        self._path_text.draw(window)
        super().draw(window)
        self._selected_text.draw(window)

    def _set_path_text_value(self, value: str) -> None:
        """Sets the value of the path text. Used to update the path text, as it should be right_aligned if too long."""
        if len(value) > self._width:
            value = value[-self._width :]
        else:  # append spaces to fill the width
            value += " " * (self._width - len(value))
        self._path_text.set_text(value)

    def _go_up(self) -> None:
        """Go up one directory."""
        _res_parent = self._path.parent.resolve()
        if _res_parent != self._path.resolve() or os.name != "nt":  # if not root or on Linux
            self._path = _res_parent
            self._set_path_text_value(str(self._path))
            self._build_choices()
            self.set_choice(0)
        else:  # on windows and root
            if self._ui:
                # self._ui.warning("Cannot go up from root directory.")
                self._set_path_text_value("My Computer")
                self._build_choices_volumes()
                self.set_choice(0)

    def _goto_directory(self, index: int) -> None:
        """Go to the directory."""
        directory = self.get_items()[self.get_choice_index()]
        newpath = (self._path / directory).resolve()
        if self.check_permission(newpath, os.R_OK):  # only if permission is granted
            self._path = newpath
            self._set_path_text_value(str(self._path))
            self._build_choices()
            if (
                self._show_current_directory and len(self.get_choices()) > 2
            ):  # if there is at least 1 item
                self.set_choice(2)
            elif (
                not self._show_current_directory and len(self.get_choices()) > 1
            ):  # if there is at least 1 item
                self.set_choice(1)
            else:
                self.set_choice(0)  # otherwise default to ".."
        if self._first_draw:
            if self.on_update:
                try_self_call(self, self.on_update)

    def check_permission(self, path: pathlib.Path, mode: int = os.R_OK) -> bool:
        """Check if the user has permission to access the path."""
        perm = os.access(path, mode)
        if not perm:
            if self._ui:
                self._ui.warning(f"Permission denied for\n{path}")
                if self._ui.logger:
                    self._ui.logger.warning(
                        f"Tried to browse with insufficient permissions for {path}"
                    )
        return perm

    def update_selected_text(self) -> None:
        """Update the selected item text."""
        if (
            self._path_text.get_text().strip() == "My Computer"
        ):  # If on Windows and selecting drives
            self._selected_text.set_text(
                GenStr(
                    (
                        self.get_items()[self.get_choice_index()],
                        None,
                        [curses.A_ITALIC, curses.A_BOLD],
                    )
                )
            )
            return

        if self.get_choice_index() < 0:
            self._selected_text.set_text("")
        elif self.get_choice_index() == 0:  # if select and item is ".."
            self._selected_text.set_text(GenStr(("{Parent directory}", None, [curses.A_ITALIC])))
        elif self._show_current_directory and self.get_choice_index() == 1:
            self._selected_text.set_text(GenStr(("{Current directory}", None, [curses.A_ITALIC])))
        else:  # normal items
            self._selected_text.set_text(
                GenStr((self.get_items()[self.get_choice_index()], None, [curses.A_ITALIC]))
            )

    def get_path(self) -> pathlib.Path:
        """Return the current path."""
        return self._path

    def key_behaviour(self, key: int) -> None:
        super().key_behaviour(key)
        self.update_selected_text()

    def _capture_take(self, origin: Tuple[int], direction: int) -> None:
        super()._capture_take(origin, direction)
        self.update_selected_text()

    def _capture_remove(self, direction: int) -> None:
        super()._capture_remove(direction)
        self._selected_text.set_text("")

    def set_palette(self, palette, should_override = False) -> None: # Override
        """Set the color palette."""
        super().set_palette(palette, should_override)
        self._selected_text.set_palette(palette, should_override)
        self._path_text.set_palette(palette, should_override)
    
