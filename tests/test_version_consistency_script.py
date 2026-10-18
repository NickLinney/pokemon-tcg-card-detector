import subprocess
import sys
from pathlib import Path


def test_version_consistency_script_passes():
    root = Path(__file__).parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "scripts" / "check_version_consistency.py")],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "released=false" in result.stdout
