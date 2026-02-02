import pytest

from src.app import app as flask_app
from src.app import db
from src.house import House
from src.demographic import Demographic

@pytest.fixture
def app():
    # Setup: Force the app to use an in-memory database
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })

    with flask_app.app_context():
        db.create_all()

        h1 = House(id="hash1", status="for_sale", price=100000.0, bed=1, zip_code=111)
        h2 = House(id="hash2", status="for_sale", price=200000.0, bed=2, zip_code=222)
        h3 = House(id="hash3", status="for_sale", price=300000.0, bed=3, zip_code=333)
        d1 = Demographic(zip_code=111, median_income=111)
        d2 = Demographic(zip_code=222, median_income=222)
        # zip_code 333 does not exists in demographics

        db.session.add_all([h1, h2, h3, d1, d2])
        db.session.commit()

        yield flask_app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()