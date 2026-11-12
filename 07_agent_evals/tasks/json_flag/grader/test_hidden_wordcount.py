import json
import subprocess
import sys

import pytest


@pytest.fixture
def sample(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("one two\nthree\n")
    return path


def cli(*args):
    proc = subprocess.run([sys.executable, "wordcount.py", *map(str, args)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_json_flag_prints_counts(sample):
    assert json.loads(cli(sample, "--json")) == {"lines": 2, "words": 3, "chars": 14}


def test_plain_output_is_unchanged(sample):
    assert cli(sample) == f"2 3 14 {sample}\n"
