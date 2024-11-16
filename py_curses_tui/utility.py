import curses
from dataclasses import dataclass
from inspect import signature
from math import ceil
from threading import Lock, Thread
from time import sleep
from typing import TYPE_CHECKING, Any, Callable, Self, Tuple

if TYPE_CHECKING:
    from .core import UserInterface

# ==== type aliases ====
Point = Tuple[int, int]
cwin = curses.window
ColorPair = Tuple[int, int]
cp = curses.color_pair

# ==== Constants ====
# should be higher than maximum of number of lines and columns. For linux, that limit is 100 so 256 should be fine.
MAX_DELTA: int = 256


# ==== Utility functions and constants ====
def set_value(var: Any, value: Any) -> None:
    """Set the value of a variable.

    Example usage: make a lambda syntax set a value
        lambda: user_interface.set_value(ui.running, False)
    """
    var = value


def inserted_text(string: str, toinsert: str, position: int) -> str:
    """Insert a string at a given position in another string."""
    return string[:position] + toinsert + string[position:]


@dataclass
class CallableSignature:
    """Dataclass to store the number of arguments of a callable."""

    required_params: int
    optional_params: int
    total_params: int

    @classmethod
    def from_callable(cls, func: Callable) -> Self:
        sig = signature(func)
        parameters = sig.parameters

        required_params = len([p for p in parameters.values() if p.default == p.empty])
        optional_params = len([p for p in parameters.values() if p.default != p.empty])
        total_params = len(parameters)

        return cls(required_params, optional_params, total_params)


def try_self_call(selfo: Any, action: Callable) -> None:
    """Try to call the action with given object as 'self', if it fails, call without it."""
    cs = CallableSignature.from_callable(action)
    if cs.required_params == 1:
        action(selfo)
    elif cs.required_params == 0:
        action()
    else:
        raise TypeError(
            f"{action} cannot have more than 1 required parameter ! : {cs.total_params}"
        )


def calls(*functions: Callable) -> Callable:
    """Create a callable that calls all given functions."""

    def calls() -> None:
        for func in functions:
            func()

    return calls


class CountDownObject:
    """Countdown from duration to 0 in steps of precision using threading."""

    def __init__(
        self,
        set_text_callable: Callable[[float], None],
        ui: "UserInterface",
    ):
        """Countdown from duration to 0 in steps of precision using threading.

        Args:
            set_text_callable (Callable[[float], None]): A callable that will be used to set the text
            ui (UserInterface): The UserInterface object

        Example usage:
            def text_drawable_countdown_set_text(left: float) -> None:
                text_drawable.set_text(
                    UI.GenStr(
                        UI.AttrStr("Please wait "),
                        UI.AttrStr(f"{left:.1f}", None, [curses.A_BOLD]),
                        UI.AttrStr(" seconds..."),
                    )
                )
            countdown_object = UI.CountDownObject(text_drawable_countdown_set_text, ui)
            try:
                countdown_object.start(10.0, 0.1)
            except KeyboardInterrupt:
                countdown_object.stop() # forcibly stops in case of keyboard interrupt

        """

        self.set_text_callable = set_text_callable
        self.ui = ui
        self.lock = Lock()
        with self.lock:
            self.RUNNING = True

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
                    self.RUNNING.set(False)
            except Exception:
                pass
        except Exception as e:
            raise e from e

    def __thread_countdown(
        self, duration: float, tocall: Callable[[float], None] = None, step: float = 0.1
    ) -> None:
        factor = 10**step
        left = ceil((duration + step) * factor) / factor
        while left >= -step and self.RUNNING:
            left -= step
            if left < 0.0:
                left = 0.0

            with self.lock:
                tocall(left)
                self.ui.mid_update()

            sleep(step)
            if left <= 0.0:
                break

    def start(self, duration: float, step: float = 0.1) -> None:
        """Start the countdown.

        Args:
            duration (float): The duration of the countdown.
            step (float, optional): The precision of the countdown (step in seconds). Defaults to 0.1.
        """
        self.__threader(
            self.__thread_countdown, duration=duration, tocall=self.set_text_callable, step=step
        )

    def stop(self) -> None:
        """Forcibly stop the countdown."""
        with self.lock:
            self.RUNNING = False
