import copy as cp
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select

from app import app
from db import get_db
from models.models import Author, AuthorCreate, Book
from routers.author import auth
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

# conftest.py pour setup les fixtures communes à tous les tests


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


def test_get_author_success(client):
    response = client.get("/author/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "first_name": "George",
        "last_name": "Orwell",
        "nationality": "English",
        "date_of_birth": "1903-06-25",
        "date_of_death": None,
        "books": [
            {
                "edition": "First edition",
                "id": 1,
                "isbn": "000-0000000000",
                "language": "English",
                "publication_date": "2018-01-01",
                "title": "Deadpond",
            },
        ],
    }


def test_create_author_success(client, session: Session):
    new_author = AuthorCreate(
        first_name="JK",
        last_name="Rowling",
        nationality="English",
        date_of_birth=date(1965, 7, 31),
    )
    response = client.post("/author/", json=json.loads(new_author.model_dump_json()))
    assert response.status_code == 200
    assert response.json()["last_name"] == "Rowling"

    author: Author = session.exec(
        select(Author).filter(Author.last_name == "Rowling")
    ).one()
    assert author.first_name == new_author.first_name
    assert author.last_name == new_author.last_name
    assert author.nationality == new_author.nationality
    assert author.date_of_birth == new_author.date_of_birth
    assert author.date_of_death == new_author.date_of_death


def test_update_author_success(client, session):
    author_before_update = session.get(Author, 1)
    author_before_update = cp.deepcopy(author_before_update)

    updated_author_data = {"date_of_death": date(1950, 1, 1).isoformat()}
    response = client.put("/author/1", json=updated_author_data)
    assert response.status_code == 200
    assert response.json()["date_of_death"] == date(1950, 1, 1).isoformat()

    author: Author = session.get(Author, 1)
    assert author.first_name == author_before_update.first_name
    assert author.last_name == author_before_update.last_name
    assert author.nationality == author_before_update.nationality
    assert author.date_of_birth == author_before_update.date_of_birth
    assert author.date_of_death != author_before_update.date_of_death


def test_delete_author_success(client, session):
    author_id = (
        session.exec(select(Author).filter(Author.last_name == "Huxley")).one().id
    )
    response = client.delete(f"/author/{author_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Author id {author_id} deleted successfully"}
    author = session.exec(select(Author).filter(Author.last_name == "Huxley")).all()
    assert author == []
    book = session.exec(select(Book).filter(Book.isbn == "000-0000000001")).one()
    assert book.authors == []


def test_create_author_missing_field(client):
    new_author = {
        "first_name": "JK",
        "nationality": "English",
        "date_of_birth": date(1965, 7, 31).isoformat(),
    }
    response = client.post("/author/", json=new_author)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "last_name"],
                "msg": "Field required",
                "input": {
                    "first_name": "JK",
                    "nationality": "English",
                    "date_of_birth": date(1965, 7, 31).isoformat(),
                },
                "url": "https://errors.pydantic.dev/2.6/v/missing",
            }
        ]
    }


def test_update_nonexistent_author(client):
    updated_author_data = {"date_of_death": "2024-01-01"}
    response = client.put("/author/999", json=updated_author_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Author id 999 not found"


def test_delete_nonexistent_author(client):
    response = client.delete("/author/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Author id 999 not found"}
