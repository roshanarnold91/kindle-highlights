import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_tmp_data_dir = tempfile.mkdtemp(prefix="khm-test-")
os.environ["DATA_DIR"] = _tmp_data_dir
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "test-admin-password"

from app import app as flask_app  # noqa: E402


@pytest.fixture()
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c
