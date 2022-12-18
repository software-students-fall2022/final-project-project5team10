import pytest
from app import app



@pytest.fixture(scope='session')
def flask_app():
    app.config.update({'TESTING': True,'LOGIN_DISABLED':False})
    with app.test_client() as client:
        yield client
