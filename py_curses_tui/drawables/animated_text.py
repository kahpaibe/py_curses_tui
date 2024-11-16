import curses
from threading import Lock, Thread
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, List, Optional

from ..utility import cwin, try_self_call
from .base_classes import AttrStr, Drawable, GenStr

if TYPE_CHECKING:
    from ..core import UserInterface

# === Some loading animations, import them if necessary ===

# ⠇⠋⠙⠸⠴⠦
LOADING1 = "\u2807\u280B\u2819\u2838\u2834\u2826"

# ⠇⠋⠙⠸⢰⣠⣄⡆
LOADING2 = "\u2807\u280B\u2819\u2838\u28B0\u28E0\u28C4\u2846"

# ⠋⠙⠚⠓
LOADING3 = "\u280B\u2819\u281A\u2813"

# ⠃⠋⠉⠙⠘⠚⠒⠓
LOADING4 = "\u2803\u280B\u2809\u2819\u2818\u281A\u2812\u2813"

# ⠇ ,⠋ ,⠉⠁,⠈⠃, ⠇,⠠⠆,⠤⠄,⠦
LOADING5 = [
    "\u2807 ",
    "\u280B ",
    "\u2809\u2801",
    "\u2808\u2803",
    " \u2807",
    "\u2820\u2806",
    "\u2824\u2804",
    "\u2826 ",
]

# ←↖↑↗→↘↓↙
LOADING6 = "\u2190\u2196\u2191\u2197\u2192\u2198\u2193\u2199"

# ▁▂▃▄▅▆▇█▇▆▅▄▃
LOADING7 = "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588\u2587\u2586\u2585\u2584\u2583"

# ▉▊▋▌▍▎▏▎▍▌▋▊▉
LOADING8 = "\u2589\u258A\u258B\u258C\u258D\u258E\u258F\u258E\u258D\u258C\u258B\u258A\u2589"

# ┤┘┴└├┌┬┐
LOADING9 = "\u2524\u2518\u2534\u2514\u252C\u250C\u252C\u2510"

# |/-\\
LOADING10 = "|/-\\"

# ◇◈◆
LOADING11 = "\u25C7\u25C8\u25C6"


# ==== Drawable objects: props ====
class AnimatedText(Drawable):
    """Create an animated text object. Purpose example: loading animations."""

    def __init__(
        self,
        y: int,
        x: int,
        ui: "UserInterface",
        color_pair_id: int = 0,
        frames: List[AttrStr] | List[str] | str = LOADING1,
        start_hidden: bool = True,
        parent: Optional[Drawable] = None,
        attributes: List[int] = [],
    ):
        """Create an animated text object. Purpose example: loading animations.

        Args:
            y (int): The y coordinate of the top-left corner of the drawable.
            x (int): The x coordinate of the top-left corner of the drawable.
            ui (UserInterface): The UserInterface object that the drawable will be drawn on, used to refresh the screen.
            color_pair_id (int, optional): The color pair id of the drawable. Defaults to 0.
            frames (List[AttrStr] | List[str] | str, optional): The frames of the animation. Defaults to LOADING1.
            start_hidden (bool, optional): Whether the drawable will be hidden at start. Defaults to True.
            parent (Optional[Drawable], optional): The parent drawable of the object. Defaults to None.
            attributes (List[int], optional): The attributes to add on frames. Defaults to [].

        frames:
            frames can be a str, each character will become a frame (1 char animation).
            frames can be a list of str, each string will become a frame.
            frames can be a list of AttrStr, each AttrStr will become a frame.
        Please note that multi-line strings ARE supported.

        ColorPalette:
            Unused

        on_update:
            Called when:
                set_hidden() is called.
                start() is called.
                stop() is called.
            Supressed before first draw.

        Example usage:
            from tuilib.drawables.animated_text import LOADING2
            animated_text = AnimatedText(0, 0, ui, 0, LOADING2)
            menu.add(animated_text)

            # Start the animation
            animated_text.start(0.1) # 0.1s per frame
            ...
            animated_text.stop()

        Please note that the animation SHOULD be stopped at some point, for example if the menu changes.
        """
        super().__init__(y, x, parent)
        self.color_pair_id = color_pair_id
        self.attributes = attributes
        self.lock = Lock()
        self._hidden = True

        self._ui = ui
        self._current_frame = 0
        self.frames: List[AttrStr] = []
        self.set_frames(frames)

        self._first_draw = start_hidden  # whether it was drawn once. Sort of init

        with self.lock:
            self._running = False

    def set_hidden(self, hidden: bool) -> None:
        """Set the hidden state of the drawable."""
        if self._first_draw and self.on_update:
            try_self_call(self, self.on_update)
        with self.lock:
            self._hidden = hidden

    def draw(self, window: cwin) -> None:
        """Does nothing."""
        if not self._first_draw:
            with self.lock:
                self._first_draw = True
        self.draw_frame(window, self._current_frame)

    def draw_frame(self, window: cwin, frame_index: int) -> None:
        """Draw given frame"""
        if self._hidden:
            return
        with self.lock:
            if not self._first_draw:
                self._first_draw = True
            if len(self.frames) == 0:
                return

            y, x = self.get_yx()
            frame = self.frames[frame_index]
            lines = frame.text.split("\n")
            for i, line in enumerate(lines):
                gs = GenStr([AttrStr(line, frame.color_pair_id, frame.attributes)])
                Drawable.draw_str(gs, window, y + i, x, frame.attributes, self.color_pair_id)

    def get_current_frame(self) -> int:
        """Get the current frame index"""
        return self._current_frame

    def set_current_frame(self, frame: int) -> None:
        """Set the current frame index"""
        with self.lock:
            if frame < 0 or frame >= len(self.frames):
                raise ValueError(
                    f"Frame index out of bounds. {frame} not in [0, {len(self.frames)}-1]"
                )
            self._current_frame = frame

    def advance_frame(self) -> None:
        """Advance the frame by 1"""
        with self.lock:
            self._current_frame = (self._current_frame + 1) % len(self.frames)

    def set_frames(self, frames: List[AttrStr] | List[str] | str = "") -> None:
        """Set the frames of the animation."""
        with self.lock:
            if len(frames) == 0:
                self.frames = []
            elif isinstance(frames, str):  # separate every single characters
                self.frames = [AttrStr(frames[i]) for i in range(len(frames))]
            elif isinstance(frames[0], str):
                self.frames = [AttrStr(f) for f in frames]
            elif isinstance(frames[0], AttrStr):
                self.frames = frames

    def __threader(self, target: Callable, **args: Any) -> None:  # create a thread
        thr = Thread(target=self.__safe_thread, kwargs={"target": target, **args})
        thr.daemon = True
        thr.start()

    def __safe_thread(self, target: Callable, **args: Any) -> None:  # thread embedding
        try:
            target(**args)
        except KeyboardInterrupt:
            try:
                with self.lock:
                    self._running.set(False)
            except Exception:
                pass
            pass
        except Exception as e:
            raise e from e

    def __run(self, rate: float):
        """Run the animation"""
        while self._running:
            self.draw_frame(self._ui.stdscr, self._current_frame)
            self._ui.mid_update()
            self.advance_frame()
            sleep(rate)

    def start(self, rate: float = 0.5) -> None:
        """Start the animation.

        Args:
            rate (float, optional): The rate of the animation in seconds. Defaults to 0.5.
        """
        if self._running is False:
            self._running = True
            self.set_hidden(False)  # unhide # will also run on_update
            self.__threader(self.__run, rate=rate)

    def stop(self, hide: bool = True) -> None:
        """Stop the animation.

        Args:
            hide (bool, optional): Whether to hide the drawable. Defaults to True.
        """
        with self.lock:
            self._running = False
            self._ui.soft_update()
            self._hidden = hide

        if self._first_draw and self.on_update:
            try_self_call(self, self.on_update)
