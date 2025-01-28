import pytest
import os
from server.settings import app, db, DB_URL

if "memory" not in DB_URL and "unittest" not in DB_URL:
    raise RuntimeError(f"Invalid DB_URL: for testing {DB_URL}")

@pytest.fixture
def test_client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

