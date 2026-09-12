import os
import sys
import tempfile
from pathlib import Path

TEST_DATABASE = Path(tempfile.gettempdir()) / f"truesource-tests-{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE}"

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_sessionfinish(session, exitstatus):
    TEST_DATABASE.unlink(missing_ok=True)
