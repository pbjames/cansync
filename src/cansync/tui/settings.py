import logging
import sys
from collections.abc import Callable
from typing import Any

from cansync import utils
from cansync.api import Canvas
from cansync.const import TUI_STYLE
from cansync.tui.shared import ErrorWindow
from cansync.types import ConfigKeys
from pytermgui import Button, Container, InputField, Splitter, Window, WindowManager

logger = logging.getLogger(__name__)
_SELECT_OPTIONS = utils.same_length(
    "Canvas URL",
    "API Token",
    "Storage Path",
    "Selected Courses",
)


class SelectWindow(Window):
    """
    User can select an operation to perform which modifies some settings
    """

    def __init__(
        self,
        context: WindowManager,
        on_click: Callable,
    ):
        self.context = context

        buttons_container = Container(
            *(Button(opt, onclick=on_click, centered=True) for opt in _SELECT_OPTIONS)
        )
        exit_container = Container(Button("Done", onclick=self.exit, centered=True))

        super().__init__(
            buttons_container,
            exit_container,
        )
        self.set_title("Settings")
        self.center()

    def exit(self, _: Button) -> None:
        self.context.stop()
        sys.exit(0)


class ConfigEditWindow(Window):
    """
    Edit a specific config value via the input field
    """

    def __init__(
        self,
        context: WindowManager,
        submit_callback: Callable,
        title: str,
        prompt: str,
        **settings: str | int | bool,
    ):
        self.input_field = InputField("", prompt=prompt)
        self.context = context

        submit_container = Splitter(
            Button("Submit", onclick=self._input_on_submit_callback(submit_callback)),
            Button("Cancel", onclick=self.on_cancel),
        )

        super().__init__(
            f"[bold accent]{title}",
            self.input_field,
            "",
            submit_container,
            **settings,
        )

        self.center()

    def on_cancel(self, _: Button) -> None:
        """
        Cancel button
        """
        self.exit()

    def _input_on_submit_callback(self, callback: Callable) -> Callable[[Button], Any]:
        """
        Provides the callback function the input field text as an argument instead of
        the submit button object (discarding it)

        :returns: Wrapped callback function
        """

        def callback_with_input(_: Button) -> Any:
            return callback(self.input_field.value.rstrip())

        return callback_with_input

    def _overwrite_value(self, text: str, key: ConfigKeys) -> None:
        if not utils.valid_key(key, text):
            logger.info(f"Invalid replacements for config, {key}: {text}")
            self.context.add(ErrorWindow(self.context, "Invalid value entered."))
        else:
            utils.overwrite_config_value(key, text)
            self.exit()

    def exit(self):
        self.context.remove(self)


class URLInputWindow(ConfigEditWindow):
    def __init__(self, context: WindowManager):
        super().__init__(context, self.on_submit, "Change Canvas URL", "Canvas URL: ")

    def on_submit(self, text: str):
        # this might come back to bite ass later
        if not text.startswith("http"):
            text = "https://" + text
        self._overwrite_value(text.strip("/"), "url")


class APIKeyInputWindow(ConfigEditWindow):
    def __init__(self, context: WindowManager):
        super().__init__(
            context, self.on_submit, "Change API token", "API token: ", width=90
        )

    def on_submit(self, text: str):
        self._overwrite_value(text, "api_key")


class StorageInputWindow(ConfigEditWindow):
    def __init__(self, context: WindowManager):
        super().__init__(
            context, self.on_submit, "Change storage path", "Path('~' ok!): "
        )

    def on_submit(self, text: str):
        self._overwrite_value(text, "storage_path")


class CoursesWindow(Window):
    """
    Show a list of courses as checkboxes and append select courses' ids to the config
    file
    """

    def __init__(self, context: WindowManager, canvas: Canvas):
        self.context = context
        self.canvas = canvas
        self.course_id: dict[str, int] = {}
        self.enabled = Container()
        self.disabled = Container()
        self.submit = Container(Button("Submit", onclick=self.on_submit, centered=True))

        super().__init__(
            "[bold]Disabled",
            "",
            self.disabled,
            "[bold]Enabled",
            "",
            self.enabled,
            self.submit,
            **TUI_STYLE,
        )

        self.center()

        config = utils.get_config()

        for name, id in self.canvas.get_courses_info():
            max_length = TUI_STYLE["width"] - 14
            shortened_name = utils.short_name(name, max_length)

            self.course_id[shortened_name] = id
            course_button = Button(shortened_name, onclick=self.on_button_click)
            if id in config["course_ids"]:
                self.enabled += course_button
            else:
                self.disabled += course_button
            self.height += 1

    def on_button_click(self, button: Button) -> None:
        def swap_container(button: Button, con1: Container, con2: Container) -> None:
            """
            Swap button from con1 -> con2 AND retain selection position
            """
            idx = con1._widgets.index(button)

            con1.remove(button)
            con2 += button

            if idx > 0:
                con1.select(idx)

        if button in self.disabled:
            swap_container(button, self.disabled, self.enabled)
        elif button in self.enabled:
            swap_container(button, self.enabled, self.disabled)

    def on_submit(self, _: Button) -> None:
        utils.overwrite_config_value(
            "course_ids",
            [self.course_id[b.label] for b in self.enabled],
        )
        self.exit()

    def exit(self):
        self.context.remove(self)


class SettingsApplication:
    """
    TUI application to manage settings easily
    """

    def __init__(self):
        self.canvas = Canvas()
        self._manager = WindowManager()
        self._main_window = SelectWindow(
            self._manager,
            self.on_select_button_click,
        )

    def on_select_button_click(self, button: Button) -> None:
        """
        Select menu chooses which window to open
        """

        label = button.label
        url, api, storage, course = _SELECT_OPTIONS

        if label == url:
            self.run(URLInputWindow(self._manager))
        if label == api:
            self.run(APIKeyInputWindow(self._manager))
        if label == storage:
            self.run(StorageInputWindow(self._manager))
        if label == course:
            attempt = self.canvas.connect()
            if not attempt:
                self.run(
                    ErrorWindow(
                        self._manager,
                        "[@surface-2 bold accent]Canvas failed to connect",
                        "Either the provided URL or API token",
                        "need to be corrected in order to",
                        "connect.",
                    )
                )
            else:
                self.run(CoursesWindow(self._manager, self.canvas))

    def stop(self) -> None:
        self._manager.stop()

    def run(self, window: Window) -> None:
        with self._manager as manager:
            manager.add(window)

    def start(self) -> None:
        self.run(self._main_window)
