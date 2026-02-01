import os
import sys

sys.path.insert(0, os.path.join(os.getcwd(), "src"))

import pytest

from conf import app as flask_app
from conf import db
from house import House
from demographic import Demographic

@pytest.fixture
def app():
    # Setup: Force the app to use an in-memory database
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with flask_app.app_context():
        db.create_all()

        h1 = House(id="hash1", status="for_sale", price=500000.0, bed=3)
        h2 = House(id="hash2", status="for_sale", price=250000.0, bed=2)
        d1 = Demographic(zip_code=123, median_income=123)

        db.session.add_all([h1, h2, d1])
        db.session.commit()

        yield flask_app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()