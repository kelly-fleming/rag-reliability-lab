"""Import the source package in a fresh process without installation."""

import subprocess
import sys
from pathlib import Path


def test_import_exposes_metadata_without_side_effects(tmp_path):
    source_dir = Path(__file__).resolve().parents[1] / "src"
    script = """
import os
import pathlib
import sys

sys.path.insert(0, sys.argv[1])
before = set(pathlib.Path.cwd().rglob('*'))

def reject_operation(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind'}:
        raise AssertionError('Network operation during import')
    if event == 'open':
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(c in mode for c in 'wax+')):
            raise AssertionError('File write during import')
        if isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT):
            raise AssertionError('File write during import')

sys.addaudithook(reject_operation)
import rag_reliability_lab

assert rag_reliability_lab.__version__ == '0.1.0'
assert rag_reliability_lab.__all__ == ['__version__']
assert {name for name in vars(rag_reliability_lab) if not name.startswith('_')} == set()
assert not any(name.startswith('rag_reliability_lab.') for name in sys.modules)
assert set(pathlib.Path.cwd().rglob('*')) == before
"""
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", script, str(source_dir)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert result.stderr == ""
