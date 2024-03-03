from __future__ import annotations

import cansync.utils as utils
from cansync.types import File, Module, ModuleItem, Course, Page, CourseInfo

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional, Generator, Any

import re
import logging
import canvasapi


class Scanner(ABC):
    """
    Define an interface to aid in standardizing what data is available so we cna lazy
    load data effeciently at the users will
    """

    name: str
    id: int
    parent: Any | None

    @staticmethod
    @abstractmethod
    def load(item: Any, parent: Any) -> Scanner: ...


@dataclass
class CourseScan(Scanner):
    """
    Courses on canvas that provide modules
    """

    code: str
    course: Course
    parent: None
    name: str
    id: int

    @staticmethod
    def load(course: Course, canvas) -> CourseScan:
        return CourseScan(
            course.course_code,
            course,
            canvas,
            utils.better_course_name(course.name),
            course.id,
        )

    def get_modules(self) -> Generator[ModuleScan, None, None]:
        for module in self.course.get_modules():
            yield ModuleScan.load(module, self)


# TODO: add quizez
@dataclass
class ModuleScan(Scanner):
    """
    Modules on canvas that provide pages and attachments although more types of items
    can be added
    """

    module: Module
    parent: CourseScan
    name: str
    id: int

    @staticmethod
    def load(module: Module, parent: CourseScan) -> ModuleScan:
        return ModuleScan(module, parent, module.name, module.id)

    def get_pages(self) -> Generator[PageScan, None, None]:
        for item in self.module.get_module_items():
            if hasattr(item, "page_url"):
                yield PageScan.load(self.parent.course.get_page(item.page_url), self)

    def get_attachments(self) -> Generator[File, None, None]:
        # FIXME: this is a blight upon mine eyes
        course = self.parent
        fs_re = r"{}/courses/{}/files/([0-9]+)".format(course.parent.url, course.id)
        for item in self.module.get_module_items():
            if hasattr(item, "url"):
                if re.match(fs_re, item.url):
                    yield course.parent.get_file(int(item.url.split("/")[-1]))


# TODO: add images, files, text
@dataclass
class PageScan(Scanner):
    """
    Pages on canvas that provide some scrapable file links a long with other items at
    the discretion of the course director
    """

    page: Page
    parent: ModuleScan
    name: str
    id: int

    @staticmethod
    def load(page: Page, parent: ModuleScan) -> PageScan:
        return PageScan(page, parent, page.title, page.page_id)

    @property
    def empty(self) -> bool:
        if not hasattr(self.page, "body"):
            return True
            logging.debug(f"Page with id {self.id} has no body")
        else:
            return self.page.body is None

    def get_files(self) -> Generator[File, None, None]:
        if self.empty:
            return

        course = self.parent.parent
        fs_re = r"{}/courses/{}/files/([0-9]+)".format(course.parent.url, course.id)
        found_file_ids = re.findall(fs_re, self.page.body)

        for id in found_file_ids:
            if id is not None:
                # this really sucks
                yield course.parent.get_file(id)


class Canvas:
    """
    Library version of canvasapi.Canvas that exposes only used methods and information
    and avoids putting canvasapi stuff everywhere while utilizing the config
    """

    def __init__(self):
        config = utils.get_config()
        self.url = config["url"]
        self._canvas = canvasapi.Canvas(config["url"], config["api_key"])

    def get_file(self, id: int) -> File:
        return self._canvas.get_file(id)

    def get_course(self, id: int) -> CourseScan:
        return CourseScan.load(self._canvas.get_course(id), self)

    def get_courses_info(self) -> Generator[CourseInfo, None, None]:
        courses = self._canvas.get_courses()
        for course in courses:
            yield CourseInfo(course.name, course.id)
