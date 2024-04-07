import copy as cp
import json
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app import app
from db import get_db
from models.models import Checkout, CheckoutCreate, Copy
from routers.checkout import auth
from setup import (
    create_authors_and_books,
    create_checkouts,
    create_copies,
    create_members,
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = Session(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(bind=engine)
    create_authors_and_books(engine)
    create_members(engine)
    create_copies(engine)
    create_checkouts(engine)

    db = TestingSessionLocal

    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):

    # Dependency override
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[auth.verify] = lambda: True

    yield TestClient(app)


def test_get_checkout_success(client):
    response = client.get("/checkout/1")
    assert response.status_code == 200
    assert response.json() == {
        "checkout_date": "2021-01-01",
        "expected_return_date": "2021-01-15",
        "member_id": 1,
        "copy_id": 1,
        "id": 1,
        "returned_date": "2021-01-10",
        "current_owner": {
            "auth0_id": "a012f_ab23f_1234f",
            "first_name": "John",
            "last_name": "Doe",
            "age": 34,
            "birthdate": "1990-01-01",
            "city": "New York",
            "membership_expiration": "2022-01-01",
            "id": 1,
        },
        "copy_item": {
            "barcode": "0100101010",
            "location": "Shelf 1",
            "is_available": True,
            "book_id": 1,
            "id": 1,
        },
    }


def test_create_checkout_success(client, session: Session):
    member_id = 2
    copy_id = 1
    new_checkout = CheckoutCreate(
        checkout_date=date.today(),
        expected_return_date=date.today() + timedelta(days=7),
        member_id=member_id,
        copy_id=copy_id,
    )
    response = client.post(
        "/checkout/", json=json.loads(new_checkout.model_dump_json())
    )
    assert response.status_code == 200
    assert response.json() == {
        "checkout_date": date.today().isoformat(),
        "expected_return_date": (date.today() + timedelta(days=7)).isoformat(),
        "member_id": member_id,
        "copy_id": copy_id,
        "id": 3,
        "returned_date": None,
    }

    checkout: Checkout = session.exec(
        select(Checkout)
        .filter(Checkout.member_id == member_id)
        .filter(Checkout.copy_id == copy_id)
        .filter(Checkout.checkout_date == date.today())
    ).one()
    assert checkout.current_owner.id == new_checkout.member_id
    assert checkout.checkout_date == new_checkout.checkout_date
    assert checkout.expected_return_date == new_checkout.expected_return_date
    assert checkout.copy_item.id == new_checkout.copy_id


def test_update_checkout_success(client, session):
    checkout_id = 2
    checkout_before_update = session.get(Checkout, checkout_id)
    checkout_before_update = cp.deepcopy(checkout_before_update)

    updated_checkout_data = {"returned_date": date(2024, 3, 15).isoformat()}
    response = client.put(f"/checkout/{checkout_id}", json=updated_checkout_data)
    assert response.status_code == 200
    assert response.json() == {
        "checkout_date": date(2024, 3, 10).isoformat(),
        "expected_return_date": date(2024, 3, 15).isoformat(),
        "member_id": 2,
        "copy_id": 2,
        "id": checkout_id,
        "returned_date": date(2024, 3, 15).isoformat(),
    }

    checkout: Checkout = session.get(Checkout, checkout_id)
    assert checkout.id == checkout_before_update.id
    assert checkout.checkout_date == checkout_before_update.checkout_date
    assert checkout.returned_date == date(2024, 3, 15)
    assert checkout.returned_date != checkout_before_update.returned_date
    assert checkout.member_id == checkout_before_update.member_id
    assert checkout.copy_id == checkout_before_update.copy_id

    # Check if copy is available after the book is returned
    copy: Copy = session.get(Copy, checkout.copy_id)
    assert copy.is_available


def test_delete_checkout_success(client, session):
    checkout_id = 1
    response = client.delete(f"/checkout/{checkout_id}")
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Checkout id {checkout_id} deleted successfully"
    }
    checkout = session.get(Checkout, checkout_id)
    assert checkout is None


def test_create_checkout_copy_not_available(client, session: Session):
    new_checkout = CheckoutCreate(
        checkout_date=date.today(),
        expected_return_date=date.today() + timedelta(days=7),
        member_id=1,
        copy_id=2,
    )
    response = client.post(
        "/checkout/", json=json.loads(new_checkout.model_dump_json())
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Copy id 2 is not available"}


def test_create_checkout_membership_expired(client, session: Session):
    member_id = 1
    new_checkout = CheckoutCreate(
        checkout_date=date.today(),
        expected_return_date=date.today() + timedelta(days=7),
        member_id=member_id,
        copy_id=1,
    )
    response = client.post(
        "/checkout/", json=json.loads(new_checkout.model_dump_json())
    )
    assert response.status_code == 404
    assert response.json() == {"detail": f"Member id {member_id} membership expired"}


def test_delete_checkout_not_returned(client, session):
    checkout_id = 2
    checkout = session.get(Checkout, checkout_id)
    assert checkout.returned_date is None

    response = client.delete(f"/checkout/{checkout_id}")
    assert response.status_code == 404
    assert response.json() == {
        "detail": (
            f"Checkout id {checkout_id} is not returned. "
            f"Please make sure the book was returned before deleting the checkout"
        )
    }


def test_create_checkout_missing_field(client):
    new_checkout = {
        "expected_return_date": "2021-01-15",
        "member_id": 1,
        "copy_id": 1,
    }
    response = client.post("/checkout/", json=new_checkout)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "checkout_date"],
                "msg": "Field required",
                "input": {
                    "expected_return_date": "2021-01-15",
                    "member_id": 1,
                    "copy_id": 1,
                },
                "url": "https://errors.pydantic.dev/2.6/v/missing",
            }
        ]
    }


def test_update_nonexistent_checkout(client):
    updated_checkout_data = {"returned_date": date.today().isoformat()}
    response = client.put("/checkout/999", json=updated_checkout_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Checkout id 999 not found"


def test_delete_nonexistent_checkout(client):
    response = client.delete("/checkout/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Checkout id 999 not found"}
