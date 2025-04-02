import os
from pathlib import Path

import pytest
from cansync import utils


@pytest.fixture
def test_data_path() -> Path:
    return Path("tests/files")


@pytest.fixture
def tmp_config_path(tmp_path) -> Path:
    return Path(tmp_path) / "config.toml"


@pytest.fixture
def config(tmp_config_path) -> bool:
    utils.create_config(tmp_config_path)
    yield utils.get_config(tmp_config_path)
    os.remove(tmp_config_path)
