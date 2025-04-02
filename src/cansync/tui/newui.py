import logging
import sys
from collections.abc import Callable
from typing import Any

from cansync import utils
from cansync.api import Canvas
from cansync.const import TUI_STYLE

# TODO: Remove
from cansync.tui.settings import SelectWindow
from cansync.tui.shared import ErrorWindow
from cansync.types import ConfigKeys
from pytermgui import (
    Button,
    Container,
    InputField,
    Splitter,
    Window,
    WindowManager,
)

logger = logging.getLogger(__name__)


class Application:
    def __init__(self) -> None:
        self._manager = WindowManager()
        self._main_window = Window()
        self._aux_window = Window()

    def stop(self) -> None:
        self._manager.stop()

    def run(self) -> None:
        with self._manager as manager:
            manager.layout.add_slot("left")
            manager.layout.add_slot("right", width=0.65)
            manager.layout.add_break()
            manager.layout.add_slot("footer", height=1)

            manager.add(self._aux_window, "left")
            manager.add(self._main_window, "right")

    def start(self) -> None:
        self.run()


if __name__ == "__main__":
    app = Application()
    app.run()
