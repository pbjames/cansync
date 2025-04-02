from pathlib import Path

import pytest
import toml
from cansync import utils


class TestUtils:
    def test_short_name(self):
        long = "Very Super Long Course Name (Longer now!!!)"
        assert utils.short_name(long, 5) == "Ver.."
        assert long == utils.short_name(long, len(long))

    def test_course_name(self):
        long = "Brilliant Course (212381, 378182)"
        assert utils.better_course_name(long) == "Brilliant Course"

        long = "Brilliant Course (By Bob and John) (918212, )"
        assert utils.better_course_name(long) == "Brilliant Course (By Bob and John)"

    def test_create_dir(self, tmp_path):
        path = Path(tmp_path) / "test2" / "test3"
        utils.create_dir(path)
        assert path.exists() and path.is_dir()

    def test_create_config(self, tmp_config_path, config):
        assert tmp_config_path.is_file()

    @pytest.mark.parametrize(
        "config_fn,test_type",
        [
            ["config_1.toml", "complete"],
            ["config_2.toml", "incomplete"],
            ["config_3.toml", "invalid"],
        ],
    )
    def test_config_properties(
        self, test_data_path: Path, config_fn: str, test_type: str
    ):
        with open(test_data_path / config_fn) as fp:
            this_config = toml.load(fp)

        expected = not test_type.startswith("in")
        if test_type.endswith("complete"):
            assert utils.complete(this_config) == expected
        elif test_type.endswith("valid"):
            assert utils.valid(this_config) == expected

    def test_get_config(self, tmp_config_path, tmp_path, config):
        assert utils.get_config() == config

    def test_set_config(self, config):
        config["url"] = "https://test2.com"
        utils.set_config(config)
        assert utils.get_config(config) == config

    def test_overwrite_config(self, config):
        utils.overwrite_config_value(
            "course_ids",
            [
                69420,
            ],
        )
        assert utils.get_config()["course_ids"] == [
            69420,
        ]

    def test_download(self): ...
