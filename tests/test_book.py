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
from models.models import BookCreate, BookUpdate, Book
import json
import copy as cp

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

    yield TestClient(app)


def test_get_book_success(client):
    response = client.get("/book/1")
    assert response.status_code == 200
    assert response.json()["title"] == "Deadpond"


def test_create_book_success(client, session):
    new_book = BookCreate(
        title="New Book",
        isbn="000-0000000003",
        edition="First edition",
        publication_date="2023-01-01",
        language="English",
        authors_ids=[1],
    )
    response = client.post("/book/", json=json.loads(new_book.model_dump_json()))
    assert response.status_code == 200
    assert response.json()["title"] == "New Book"

    book = session.exec(select(Book).filter(Book.isbn == "000-0000000003")).one()
    assert book.title == new_book.title
    assert book.isbn == new_book.isbn
    assert book.edition == new_book.edition
    assert book.publication_date == new_book.publication_date
    assert book.language == new_book.language


def test_update_book_success(client, session):
    book_before_update = session.get(Book, 1)
    book_before_update = cp.deepcopy(book_before_update)

    updated_book_data = {"title": "Updated Book Title", "authors_ids": [2]}
    response = client.put("/book/1", json=updated_book_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Book Title"

    book = session.get(Book, 1)
    assert book.title == "Updated Book Title"
    assert book.title != book_before_update.title
    assert book.isbn == book_before_update.isbn
    assert book.edition == book_before_update.edition
    assert book.publication_date == book_before_update.publication_date
    assert book.language == book_before_update.language
    assert len(book.authors) == 1
    assert book.authors[0].id == 2


def test_delete_book_success(client, session):
    book_id = session.exec(select(Book).filter(Book.isbn == "000-0000000002")).one().id
    response = client.delete(f"/book/{book_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Book id {book_id} deleted successfully"}
    book = session.exec(select(Book).filter(Book.isbn == "000-0000000002")).all()
    assert book == []


def test_create_book_missing_field(client):
    new_book = {
        "isbn": "000-0000000003",
        "edition": "First edition",
        "publication_date": "2023-01-01",
        "language": "English",
        "authors_ids": [1],
    }
    response = client.post("/book/", json=new_book)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "title"],
                "msg": "Field required",
                "input": {
                    "isbn": "000-0000000003",
                    "edition": "First edition",
                    "publication_date": "2023-01-01",
                    "language": "English",
                    "authors_ids": [1],
                },
                "url": "https://errors.pydantic.dev/2.6/v/missing",
            }
        ]
    }


def test_update_nonexistent_book(client):
    updated_book_data = {"title": "Updated Book Title", "authors_ids": [2]}
    response = client.put("/book/999", json=updated_book_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Book id 999 not found"


def test_delete_nonexistent_book(client):
    response = client.delete("/book/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Book id 999 not found"}
