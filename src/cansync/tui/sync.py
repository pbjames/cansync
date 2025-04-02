from __future__ import annotations

import logging
import sys

from cansync import utils
from cansync.api import Canvas, CourseScan, ModuleScan, PageScan
from cansync.types import File
from pytermgui import Button, Container, Window, WindowManager

logger = logging.getLogger(__name__)


class SyncWindow(Window):
    def __init__(self, context: WindowManager, canvas: Canvas):
        self.context = context
        self.canvas = canvas
        self.title = "Sync"
        self.download_count = 0
        self.sync_button = Button("Sync all", onclick=self.sync)
        self.exit_button = Button("  Exit  ", onclick=self.exit)
        super().__init__(self.sync_button, self.exit_button, box="DOUBLE", width=22)
        self.center()

    def action(self, course: CourseScan, module: ModuleScan, action: str) -> None:
        super().__init__(
            Container(
                f"Course: {course.name}",
                f"Module: {module.name}",
                f"[bold accent]{action}",
                "Press Ctrl-C to stop me!",
            ),
            width=70,
        )
        self.center()  # this sux

    def finish(self) -> None:
        super().__init__(
            f"[!rainbow]Finished with {self.download_count} new files!",
            self.exit_button,
        )

    def sync(self, button: Button) -> None:
        for course in self.canvas.get_courses():
            for module in course.get_modules():
                for attachment in module.get_attachments():
                    self.action(course, module, "Downloading attachments...")
                    self.download(attachment, None, course, module)

                for page in module.get_pages():
                    self.action(course, module, "Reading page...")

                    for file in page.get_files():
                        self.action(
                            course, module, f"Downloading file [{file.filename}]..."
                        )
                        self.download(file, page, course, module)

        self.finish()

    def download(
        self,
        file: File,
        page: PageScan | None,
        course: CourseScan,
        module: ModuleScan,
    ) -> None:
        logger.info(f"Downloading {file.filename}")
        names = (course.name, module.name, page.name if page is not None else None)
        names = (utils.path_format(name) for name in names if name is not None)

        new = utils.download_structured(file, *names)
        if not new:
            self.action(course, module, "Skipping file...")
        else:
            self.download_count += 1

    def exit(self, _: Button) -> None:
        self.context.stop()


class SyncApplication:
    def __init__(self):
        self._manager = WindowManager()
        self.canvas = Canvas()

        if self.canvas.connect():
            self.main_window = SyncWindow(self._manager, self.canvas)
        else:
            from cansync.tui.shared import ErrorWindow

            self.main_window = ErrorWindow(
                self._manager,
                "You need to configure the settings before downloading stuff, try:",
                "[@surface-2 !gradient(210)]cansync settings",
                "in the command line.",
                on_done=exit,
            )

    def run(self, window: Window):
        with self._manager as manager:
            manager.add(window)

    def start(self):
        try:
            self.run(self.main_window)
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
