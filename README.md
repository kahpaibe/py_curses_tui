# py_curses_tui

Library based on curses for creating terminal-based user interfaces (TUI). Cross compatible with Windows and Linux systems.

# Requirements

- `Python 3.11+`
- `curses` (`windows-curses` on windows, `ncurses` on linux)

# How to use

Please refer to the `example.py` file for a simple example of how to use the library.

## Main concepts

This library extensively uses the oriented-object approach. In *py_curses_tui*, the main object categories are:

- `UserInterface` (ui) : the main application object that will handle the behaviour and drawing loop
- `Menu` (m) : a screen that will be shown by the ui, containing Drawable objects
- `Drawable` (d) : Generic object that can be drawn on the screen.
- `KeyCaptureDrawable` (kcd) : Drawable that can capture key events and thus allow for behaviour using key presses

A UserInterface object will thus be created containing one or several menus, and its behaviour and drawing loop should be wrapped in a curses.wrapper environment.

## About menus

A `Menu` object can be used in two ways:

- As a background menu, when in the ui.menus dict. Such a menu would be drawn by the ui if it is the current selected menu
- As a top menu, which allows for pop ups and drawings above below menus (background menus being the lowest layer)

### Navigation and submenus

When a menu contains `KeyCaptureDrawable` objects, the library will handle the ability to move between them using the arrow keys.

*py_curses_tui* allows priotizing navigation inside a block, categorized by a `Submenu` object. The navigation will first try to find a nice canditate to jump to inside the submenu that the current kcd is in, and then try to find a nice candidate in the other submenus. When adding a kcd, the user may specify a submenu to add it to.

The best jump candidate is determined by sorting all other kcds using a custom distance function which represents the priority according to some position. To do this, a `Hitbox` object is used to represent the position of the kcd. *py_curses_tui* allows for setting custom hitboxes for kcds to allow for finer control over the navigation.
