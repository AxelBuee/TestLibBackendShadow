import pytest
from fastapi.testclient import TestClient
from app import app
from setup import (
    create_authors_and_books,
    create_members,
    create_checkouts,
    create_copies,
)
from db import get_db
from sqlmodel import create_engine, Session, SQLModel, select
from models.models import CopyCreate, Copy
import copy as cp
from routers.copy import auth

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


def test_get_copy_success(client):
    response = client.get("/copy/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "barcode": "0100101010",
        "book_id": 1,
        "checkouts": [
            {
                "checkout_date": "2021-01-01",
                "copy_id": 1,
                "expected_return_date": "2021-01-15",
                "id": 1,
                "member_id": 1,
                "returned_date": "2021-01-10",
            }
        ],
        "is_available": True,
        "location": "Shelf 1",
    }


def test_create_copy_success(client, session: Session):
    new_copy = CopyCreate(
        barcode="0000111001011", location="Shelf 2", is_available=True, book_id=1
    )
    response = client.post("/copy/", json=new_copy.model_dump())
    assert response.status_code == 200
    assert response.json()["barcode"] == "0000111001011"

    copy: Copy = session.exec(
        select(Copy).filter(Copy.barcode == "0000111001011")
    ).one()
    assert copy.barcode == new_copy.barcode
    assert copy.location == new_copy.location
    assert copy.is_available == new_copy.is_available
    assert copy.book_id == new_copy.book_id


def test_update_copy_success(client, session):
    copy_before_update = session.get(Copy, 1)
    copy_before_update = cp.deepcopy(copy_before_update)

    updated_copy_data = {"location": "Shelf 3"}
    response = client.put("/copy/1", json=updated_copy_data)
    assert response.status_code == 200
    assert response.json()["location"] == "Shelf 3"

    copy: Copy = session.get(Copy, 1)
    assert copy.barcode == copy_before_update.barcode
    assert copy.location == "Shelf 3"
    assert copy.location != copy_before_update.location
    assert copy.is_available == copy_before_update.is_available
    assert copy.book_id == copy_before_update.book_id


def test_delete_copy_success(client, session):
    copy_id = session.exec(select(Copy).filter(Copy.barcode == "1100100000")).one().id
    response = client.delete(f"/copy/{copy_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Copy id {copy_id} deleted successfully"}
    copy = session.exec(select(Copy).filter(Copy.barcode == "1100100000")).all()
    assert copy == []


def test_create_copy_missing_field(client):
    new_copy = {
        "book_id": 2,
        "is_available": True,
        "location": "Back storage",
    }
    response = client.post("/copy/", json=new_copy)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "barcode"],
                "msg": "Field required",
                "input": {
                    "book_id": 2,
                    "is_available": True,
                    "location": "Back storage",
                },
                "url": "https://errors.pydantic.dev/2.6/v/missing",
            }
        ]
    }


def test_update_nonexistent_copy(client):
    updated_copy_data = {"location": "Front desk"}
    response = client.put("/copy/999", json=updated_copy_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Copy id 999 not found"


def test_delete_nonexistent_copy(client):
    response = client.delete("/copy/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Copy id 999 not found"}
