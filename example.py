from py_curses_tui import core as UI
import curses
from typing import Final
from dataclasses import dataclass
import logging

import sys
import os

# Add the parent directory of `folder1` to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)

# === Generic definitions ===
H : Final[int] = 24
W : Final[int] = 80

@dataclass
class ColorPaletteW(UI.ColorPalette):
    """Color palette (light theme)"""

    text: int = 12  # text color
    box: int = 12  # box borders and background
    cursor: int = 8  # current "mouse over" item
    scrollbar: int = 4  # scrollbars
    button_selected: int = -12  # selected button
    button_unselected: int = -16  # unselected button

    box_hover: int = -4  # hover color for boxes
    box_selected: int = 4  # selected color for boxes
    # == Palette for text edit objects ==
    text_edit_text: int = -12  # text in text input objects
    text_edit_inactive: int = -12  # text input objects when not active
    text_edit_full: int = 17  # if line is full
    text_edit_cursor: int = -12  # cursor in text input objects
    text_edit_hover: int = -14  # color when hovering text input without activating it
    # == Palette for file explorer objects ==
    file_explorer_file: int = 0  # file in file explorer
    file_explorer_directory: int = 6  # directory in file explorer
    file_explorer_dots: int = 15  # dot directories (current / parent) in file explorer
    file_explorer_dim: int = 15  # dimmed text for file or directory in file explorer
    file_explorer_selected: int = 15  # selected file or directory name preview in file explorer
    file_explorer_path: int = -16  # path in file explorer
    file_explorer_scrollbar: int = 4  # scrollbar in file explorer
    # == Palette for file explorer prompt (ui.browse_file or ui.browse_directory) ==
    explorer_prompt_file: int = 12  # file or directory in file explorer
    explorer_prompt_directory: int = 13  # directory in file explorer
    explorer_prompt_dots: int = 16  # dot directories (current / parent) in file explorer
    explorer_prompt_dim: int = 16  # dimmed text for file or directory in file explorer
    explorer_prompt_selected: int = 16  # selected file or directory name preview in file explorer
    explorer_prompt_path: int = -15  # path in file explorer
    explorer_prompt_scrollbar: int = 12  # scrollbar in file explorer

def wrapped_main(stdscr: UI.cwin, logger: logging.Logger = None) -> None:
    """Main function  to wrap inside curses.wrapper. Adding a logger is optional."""
    # === Build the tui application ===
    # == Initial setup ==
    menu_main = UI.Menu( ColorPaletteW())
    menu_d1 = UI.Menu(UI.ColorPalette()) # Menu for drawables 1 (non kcd)
    menu_kcd1 = UI.Menu(UI.ColorPalette()) # Menu for kcd drawables 1
    menu_kcd2 = UI.Menu(UI.ColorPalette()) # Menu for kcd drawables 2
    menu_kcd3 = UI.Menu(UI.ColorPalette()) # Menu for kcd drawables 3
    menus = {"menu_main": menu_main,
             "menu_d1": menu_d1,
             "menu_kcd1": menu_kcd1, "menu_kcd2": menu_kcd2, "menu_kcd3": menu_kcd3}

    color_pairs = UI.get_color_pairs() # initialize color pairs
    ui = UI.UserInterface(stdscr, color_pairs, menus, "", H, W, logger=logger) # Create the UI object
    ui.set_menu("menu_main") # Set the main menu

    # == Create menus ==
    # = Main menu =
    # Create objects
    menu_main_box = UI.Box(0, 0, H, W)
    text_ = "Welcome to the Drawable Showcase!"
    menu_main_title = UI.Text(text_, 0, (W-len(text_))//2, color_pair_id=None, width=len(text_) + 2, centered=True, parent=menu_main_box)
   
    menu_main_button_drawables = UI.Button("Explore simple drawables", H-3, 3, lambda: ui.set_menu("menu_d1"), width=32, parent=menu_main_box) 
    menu_main_button_kcd = UI.Button("Explore key capture drawables", H-3, W//2 + 3, lambda: ui.set_menu("menu_kcd1"), width=32, parent=menu_main_box)

    # Add the objects to the menu
    menu_main.add(menu_main_box)
    menu_main.add(menu_main_title)
    menu_main.add_key_capture_drawable(menu_main_button_drawables,0)
    menu_main.add_key_capture_drawable(menu_main_button_kcd,0)

    ## Introduction text
    menu_main.add(UI.Text("This is an example TUI program made using py_curses_tui.", 2, 2, color_pair_id=None, parent=menu_main_box))
    menu_main.add(UI.Text("Here, dummy Drawable objects and Key Capture Drawable objects were defined.", 4, 2, color_pair_id=None, parent=menu_main_box))
    
    # = Drawables 1 menu =
    # Create base objects
    menu_d1_animated_text: UI.AnimatedText # to allow stopping the animation when leaving the menu
    menu_d1_box = UI.Box(0, 0, H, W)
    text_ = "Simple Drawables"
    menu_d1_title = UI.Text(text_, 0, (W-len(text_))//2, color_pair_id=0, width=len(text_) + 2, centered=True, parent=menu_d1_box)
    menu_d1_button_main = UI.Button("Go to main menu", H-3, 3, lambda: (ui.set_menu("menu_main"),menu_d1_animated_text.stop()), width=32,parent=menu_d1_box)
    # Add the objects to the menu
    menu_d1.add(menu_d1_box)
    menu_d1.add(menu_d1_title)
    menu_d1.add_key_capture_drawable(menu_d1_button_main,0)

    # Display drawables
    ## Box
    menu_d1_box__text = UI.Text(UI.GenStr( ("Box",None,[curses.A_BOLD]) ), 1, 2, parent=menu_d1_box)
    menu_d1_box_ = UI.Box(1, 0, 8, 8, parent=menu_d1_box__text)
    menu_d1.add(menu_d1_box__text)
    menu_d1.add(menu_d1_box_)

    ## Fill
    menu_d1_fill__text = UI.Text(UI.GenStr( ("Fill",None,[curses.A_BOLD]) ), 1, 12, parent=menu_d1_box)
    menu_d1_fill_ = UI.Fill(1, 0, 8, 8, UI.ColorPalette(box=-6), parent=menu_d1_fill__text)
    menu_d1.add(menu_d1_fill__text)
    menu_d1.add(menu_d1_fill_)

    ## Text
    menu_d1_text__text = UI.Text(UI.GenStr( ("Text",None,[curses.A_BOLD]) ), 1, 22, parent=menu_d1_box)
    genstr_ = UI.GenStr([("Hello"),(" W",1,[curses.A_BOLD,curses.A_ITALIC]),("orld !",10,[curses.A_ITALIC])]) # Allows for complex text formatting
    menu_d1_text_ = UI.Text(genstr_, 1, 0, parent=menu_d1_text__text)
    menu_d1.add(menu_d1_text__text)
    menu_d1.add(menu_d1_text_)

    ## RGBPreview
    menu_d1_rgbpreview_text = UI.Text(UI.GenStr( ("RGBPreview",None,[curses.A_BOLD]) ), 10, 2, parent=menu_d1_box)
    menu_d1_rgbpreview = UI.RGBPreview(1, 0, 8, 8, color_index=-1, pair_index=-1, parent=menu_d1_rgbpreview_text)
    menu_d1_rgbpreview.set_color_255((192,92,32))
    menu_d1.add(menu_d1_rgbpreview_text)
    menu_d1.add(menu_d1_rgbpreview)

    ## AnimatedText
    menu_d1_animated_text_text = UI.Text(UI.GenStr( ("AnimatedText",None,[curses.A_BOLD]) ), 4, 22, parent=menu_d1_box)
    menu_d1.add(menu_d1_animated_text_text)
    from py_curses_tui.drawables.animated_text import WAVE1
    menu_d1_animated_text = UI.AnimatedText(1, 0, ui, 1, WAVE1, stop_hidden=False, parent=menu_d1_animated_text_text)
    menu_d1.add(menu_d1_animated_text)
    ### Start the animation button
    def toggle_animated_text():
        if menu_d1_animated_text.is_running():
            menu_d1_animated_text.stop()
        else:
            menu_d1_animated_text.start(0.1)
    menu_d1_button_animated_text = UI.Button("Toggle animation", 1, 0, toggle_animated_text, parent=menu_d1_animated_text_text)
    menu_d1.add_key_capture_drawable(menu_d1_button_animated_text,1)

    # = KeyCaptureDrawables 1 menu =
    # Create base objects
    menu_kcd1_box = UI.Box(0, 0, H, W)
    text_ = "Key Capture Drawables 1"
    menu_kcd1_title = UI.Text(text_, 0, (W-len(text_))//2,width=len(text_) + 2, parent=menu_kcd1_box,centered=True)
    menu_kcd1_button_main = UI.Button("Go to main menu", H-3, 3, lambda: ui.set_menu("menu_main"), width=32,parent=menu_kcd1_box)
    menu_kcd1_button_kcd2 = UI.Button("Next page", H-3, W//2 + 3, lambda: ui.set_menu("menu_kcd2"), width=32,parent=menu_kcd1_box)
    # Add the objects to the menu
    menu_kcd1.add(menu_kcd1_box)
    menu_kcd1.add(menu_kcd1_title)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_button_main,0)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_button_kcd2,0)

    # Display kcds
    ## Button
    menu_kcd1_button_text = UI.Text(UI.GenStr( ("Button",None,[curses.A_BOLD]) ), 1, 2, parent=menu_kcd1_box)
    menu_kcd1_button = UI.Button("Pop up !", 1, 0, lambda: ui.prompt("Please enter some text"," PRESSED ", input_max_length=12, confirm_action=(lambda arg: ui.info(f"You just entered\n{arg}\n!"))), parent=menu_kcd1_button_text)
    menu_kcd1.add(menu_kcd1_button_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_button,1)

    ## Choose
    menu_kcd1_choose_text = UI.Text(UI.GenStr( ("Choose",None,[curses.A_BOLD]) ), 1, 15, parent=menu_kcd1_box)
    _choices = [UI.Choice(text, lambda selfochoose: ui.info(f"You selected {selfochoose.get_choice().text}")) for text in ["English", "French", "Spanish"]]
    menu_kcd1_choose = UI.Choose(1, 0, _choices, parent=menu_kcd1_choose_text)
    menu_kcd1.add(menu_kcd1_choose_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_choose,1)

    ## ScrollableChoose
    menu_kcd1_scrollablechoose_text = UI.Text(UI.GenStr( ("ScrollableChoose",None,[curses.A_BOLD]) ), 7, 15, parent=menu_kcd1_box)
    _choices = [UI.Choice(text, lambda solfo_scrollchoose: ui.info(f"You selected {solfo_scrollchoose.get_choice().text}")) for text in [f"Choice {i}" for i in range(20)]]
    menu_kcd1_scrollablechoose = UI.ScrollableChoose(1, 0, 5, _choices,scroll_type=1, parent=menu_kcd1_scrollablechoose_text)
    menu_kcd1.add(menu_kcd1_scrollablechoose_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_scrollablechoose,1)

    ## MultiSelect
    menu_kcd1_multiselect_text = UI.Text(UI.GenStr( ("MultiSelect",None,[curses.A_BOLD]) ), 1, 33, parent=menu_kcd1_box)
    _choices = [UI.Choice(text, lambda solfo_scrollchoose: ui.info(f"You selected {solfo_scrollchoose.get_choice().text}")) for text in ["Item 1", "Item 2", "Item 3"]]
    menu_kcd1_multiselect = UI.MultiSelect(1, 0, _choices, parent=menu_kcd1_multiselect_text)
    menu_kcd1.add(menu_kcd1_multiselect_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_multiselect,1)
    # button
    menu_kcd1_multiselect_button = UI.Button("Get selected", 4, 0, lambda: ui.info(f"Selected items: {[str(c.text) for c in menu_kcd1_multiselect.get_selected_choices()]}"), parent=menu_kcd1_multiselect_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_multiselect_button,1)

    ## ScrollableMultiSelect
    menu_kcd1_scrollablemultiselect_text = UI.Text(UI.GenStr( ("ScrollableMultiSelect",None,[curses.A_BOLD]) ), 7, 33, parent=menu_kcd1_box)
    _choices = [UI.Choice(text, lambda solfo_scrollchoose: ui.info(f"You selected {solfo_scrollchoose.get_choice().text}")) for text in [f"Choice {i}" for i in range(20)]]
    menu_kcd1_scrollablemultiselect = UI.ScrollableMultiSelect(1, 0, 5, _choices, scroll_type=1, parent=menu_kcd1_scrollablemultiselect_text)
    menu_kcd1.add(menu_kcd1_scrollablemultiselect_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_scrollablemultiselect,1)
    # button
    menu_kcd1_scrollablemultiselect_button = UI.Button("Get selected", 6, 0, lambda: ui.info(f"Selected items: {[str(c.text) for c in menu_kcd1_scrollablemultiselect.get_selected_choices()]}"), parent=menu_kcd1_scrollablemultiselect_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_scrollablemultiselect_button,1)

    ## SingleSelect
    menu_kcd1_singleselect_text = UI.Text(UI.GenStr( ("SingleSelect",None,[curses.A_BOLD]) ), 1, 58, parent=menu_kcd1_box)
    _choices = [UI.Choice(text, lambda solfo_scrollchoose: ui.info(f"You selected {solfo_scrollchoose.get_choice().text}")) for text in [f"Option {i}" for i in range(3)]]
    menu_kcd1_singleselect = UI.SingleSelect(1, 0, _choices, parent=menu_kcd1_singleselect_text)
    menu_kcd1.add(menu_kcd1_singleselect_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_singleselect,1)
    # button
    menu_kcd1_singleselect_button = UI.Button("Get selected", 4, 0, lambda: ui.info(f"Selected item: {menu_kcd1_singleselect.get_selected_choice().text}"), parent=menu_kcd1_singleselect_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_singleselect_button,1)

    ## Toggle
    menu_kcd1_toggle_text = UI.Text(UI.GenStr( ("Toggle",None,[curses.A_BOLD]) ), 7, 58, parent=menu_kcd1_box)
    menu_kcd1_toggle = UI.Toggle(1, 0, ["Red   ","Blue  ", "Green "], parent=menu_kcd1_toggle_text)
    menu_kcd1.add(menu_kcd1_toggle_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_toggle,1)
    # button
    menu_kcd1_toggle_button = UI.Button("Get state", 2, 0, lambda: ui.info(f"Toggle state: {menu_kcd1_toggle.get_state()}"), parent=menu_kcd1_toggle_text)
    menu_kcd1.add_key_capture_drawable(menu_kcd1_toggle_button,1)

    # = KeyCaptureDrawables 2 menu =
    # Create base objects
    menu_kcd2_box = UI.Box(0, 0, H, W)
    text_ = "Key Capture Drawables 2"
    menu_kcd2_title = UI.Text(text_, 0, (W-len(text_))//2,width=len(text_) + 2, parent=menu_kcd2_box,centered=True)
    menu_kcd2_button_kcd1 = UI.Button("Previous page", H-3, 3, lambda: ui.set_menu("menu_kcd1"), width=32,parent=menu_kcd2_box)
    # menu_kcd2_button_kcd3 = UI.Button("Next page", H-3, W//2 + 3, lambda: ui.set_menu("menu_kcd3"), width=32,parent=menu_kcd2_box)
    # Add the objects to the menu
    menu_kcd2.add(menu_kcd2_box)
    menu_kcd2.add(menu_kcd2_title)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_button_kcd1,0)
    # menu_kcd2.add_key_capture_drawable(menu_kcd2_button_kcd3,0)

    ## TextInput
    menu_kcd2_textinput_text = UI.Text(UI.GenStr( ("TextInput",None,[curses.A_BOLD]) ), 1, 2, parent=menu_kcd2_box)
    menu_kcd2_textinput = UI.TextInput(1, 0, 12, parent=menu_kcd2_textinput_text)
    menu_kcd2_textinput_button = UI.Button("Get text", 2, 0, lambda: ui.info(f"Entered text: {menu_kcd2_textinput.get_text()}"), parent=menu_kcd2_textinput_text)
    menu_kcd2.add(menu_kcd2_textinput_text)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_textinput,1)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_textinput_button,1)

    ## TextBox
    menu_kcd2_textbox_text = UI.Text(UI.GenStr( ("TextBox",None,[curses.A_BOLD]) ), 5, 2, parent=menu_kcd2_box)
    menu_kcd2_textbox = UI.TextBox(1, 0, 12, 5, False, parent=menu_kcd2_textbox_text)
    menu_kcd2_textbox_button = UI.Button("Get text", 6, 0, lambda: ui.info(f"Entered text:\n{menu_kcd2_textbox.get_text()}"), parent=menu_kcd2_textbox_text)
    menu_kcd2.add(menu_kcd2_textbox_text)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_textbox,1)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_textbox_button,1)

    ## ScrollableTextBox
    menu_kcd2_scrollabletextbox_text = UI.Text(UI.GenStr( ("ScrollableTextBox",None,[curses.A_BOLD]) ), 14, 2, parent=menu_kcd2_box)
    menu_kcd2_scrollabletextbox = UI.ScrollableTextBox(1, 0, 3, 10, scroll_type=1, text="\n".join([f"Line {i}" for i in range(20)]), parent=menu_kcd2_scrollabletextbox_text)
    menu_kcd2_scrollabletextbox_button = UI.Button("Get text", 4, 0, lambda: ui.info(f"Entered text:\n{menu_kcd2_scrollabletextbox.get_text()}"), parent=menu_kcd2_scrollabletextbox_text)
    menu_kcd2.add(menu_kcd2_scrollabletextbox_text)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_scrollabletextbox,1)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_scrollabletextbox_button,1)

    ## ScrollableTextDisplay
    lorem_ipsum = "Lorem ipsum dolor sit amet, consectetur adipiscing elit,\nsed do eiusmod tempor incididunt ut labore et dolore magna aliqua.\nUt enim ad minim veniam, quis nostrud exercitation ullamco laboris\nnisi ut aliquip ex ea commodo consequat.\nDuis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore\neu fugiat nulla pariatur.\nExcepteur sint occaecat cupidatat non proident, sunt in culpa qui officia\ndeserunt mollit anim id est laborum."
    menu_kcd2_scrollabletextdisplay_text = UI.Text(UI.GenStr( ("ScrollableTextDisplay",None,[curses.A_BOLD]) ), 1, 20, parent=menu_kcd2_box)
    menu_kcd2_scrollabletextdisplay = UI.ScrollableTextDisplay(1, 0, 5, 18, text=lorem_ipsum, scroll_type=2, parent=menu_kcd2_scrollabletextdisplay_text)
    menu_kcd2.add(menu_kcd2_scrollabletextdisplay_text)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_scrollabletextdisplay,2)

    ## FileExplorer
    menu_kcd2_fileexplorer_text = UI.Text(UI.GenStr( ("FileExplorer",None,[curses.A_BOLD]) ), 8, 20, parent=menu_kcd2_box)
    menu_kcd2_fileexplorer = UI.FileExplorer(1, 0, 10, 20, ui, parent=menu_kcd2_fileexplorer_text)
    menu_kcd2.add(menu_kcd2_fileexplorer_text)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_fileexplorer,2)

    ## DropDown
    menu_kcd2_dropdown_text = UI.Text(UI.GenStr( ("DropDown",None,[curses.A_BOLD]) ), 1, 52, parent=menu_kcd2_box)
    _options = ["Mode 1", "Mode 2", "Mode 3"]
    menu_kcd2_dropdown = UI.DropDown(1, 0, ui, _options, parent=menu_kcd2_dropdown_text)
    menu_kcd2.add(menu_kcd2_dropdown_text)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_dropdown,3)

    ## ColorSetter (Wrapped)
    menu_kcd2_colorsetter_text = UI.Text(UI.GenStr( ("ColorSetter (Wrapped)",None,[curses.A_BOLD]) ), 4, 52, parent=menu_kcd2_box)
    menu_kcd2_colorsetter = UI.ColorSetter(1, 2, ui, pair_id=UI.MAX_PAIRS, color_id=curses.COLORS - 1, color_format="FFFFFF", parent=menu_kcd2_colorsetter_text)
    menu_kcd2_colorsetter_wrapped = UI.WrapperReset(menu_kcd2_colorsetter, lambda: menu_kcd2_colorsetter.set_color((255,100,10)), True)
    menu_kcd2.add(menu_kcd2_colorsetter_text)
    menu_kcd2.add_key_capture_drawable(menu_kcd2_colorsetter_wrapped,3)
    menu_kcd2_colorsetter.set_color((255,100,10)) # Set the initial color

    ## ItemListSubmenu (This is a submenu !)
    menu_kcd2_itemlistsubmenu_text = UI.Text(UI.GenStr( ("ItemListSubmenu",None,[curses.A_BOLD]) ), 8, 52, parent=menu_kcd2_box)
    _items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"]
    menu_kcd2_itemlistsubmenu = UI.ItemListSubmenu(1,0, 12, _items, max_items=6, parent=menu_kcd2_itemlistsubmenu_text)
    menu_kcd2.add(menu_kcd2_itemlistsubmenu_text)
    menu_kcd2.set_submenu(menu_kcd2_itemlistsubmenu, len(menu_kcd2.get_submenus()))



    # Launch the UI loop
    ui.ui_loop()

if __name__ == "__main__":
    # Launch the wrapper
    UI.curses.wrapper(wrapped_main)