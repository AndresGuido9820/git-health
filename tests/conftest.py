import subprocess
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def git_repository(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
