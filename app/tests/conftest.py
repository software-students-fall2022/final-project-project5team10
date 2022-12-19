import pytest
from app import app



@pytest.fixture(scope='session')
def flask_app():
    app.config.update({'TESTING': True,'LOGIN_DISABLED':True})
    with app.test_client() as client:
        yield client
