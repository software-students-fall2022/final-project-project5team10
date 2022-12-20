import pytest
from app import app
from flask import template_rendered


@pytest.fixture(scope='session')
def flask_app():
    app.config.update({'TESTING': True,'LOGIN_DISABLED':True})
    with app.test_client() as client:
        yield client

@pytest.fixture
def captured_templates():
    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)