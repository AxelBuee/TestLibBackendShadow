import copy as cp
import json
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, col, create_engine, select

from app import app
from db import get_db
from models.models import Member, MemberCreate
from routers.member import auth
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


def test_get_member_success(client: TestClient):
    response = client.get("/member/1")
    assert response.status_code == 200
    assert response.json() == {
        "auth0_id": "a012f_ab23f_1234f",
        "first_name": "John",
        "last_name": "Doe",
        "age": 34,
        "birthdate": "1990-01-01",
        "city": "New York",
        "membership_expiration": "2022-01-01",
        "id": 1,
        "member_checkouts": [
            {
                "checkout_date": "2021-01-01",
                "expected_return_date": "2021-01-15",
                "member_id": 1,
                "copy_id": 1,
                "id": 1,
                "returned_date": "2021-01-10",
            }
        ],
    }


def test_create_member_success(client: TestClient, session: Session):
    new_member = MemberCreate(
        auth0_id="cc23e_ae873_a123b",
        first_name="TestFirstName",
        last_name="TestLastName",
        age=34,
        birthdate="1990-01-01",
        city="Paris",
        membership_expiration="2022-01-01",
    )
    response = client.post("/member/", json=json.loads(new_member.model_dump_json()))
    assert response.status_code == 200
    assert response.json() == {
        "auth0_id": "cc23e_ae873_a123b",
        "first_name": "TestFirstName",
        "last_name": "TestLastName",
        "age": 34,
        "birthdate": "1990-01-01",
        "city": "Paris",
        "membership_expiration": "2022-01-01",
        "id": 4,
    }

    member: Member = session.exec(
        select(Member).filter(Member.auth0_id == "cc23e_ae873_a123b")
    ).one()
    assert member.auth0_id == new_member.auth0_id
    assert member.first_name == new_member.first_name
    assert member.last_name == new_member.last_name
    assert member.age == new_member.age
    assert member.birthdate == new_member.birthdate
    assert member.city == new_member.city
    assert member.membership_expiration == new_member.membership_expiration


def test_update_member_success(client: TestClient, session: Session):
    member_id = 2
    member_before_update = session.get(Member, member_id)
    member_before_update = cp.deepcopy(member_before_update)

    updated_member_data = {"membership_expiration": date(2024, 3, 15).isoformat()}
    response = client.put(f"/member/{member_id}", json=updated_member_data)
    assert response.status_code == 200
    assert response.json() == {
        "auth0_id": "da33b_1234f_c0e3e",
        "first_name": "Jane",
        "last_name": "Doe",
        "age": 10,
        "birthdate": "2014-01-01",
        "city": "New York",
        "membership_expiration": "2024-03-15",
        "id": 2,
    }

    member: Member = session.get(Member, member_id)
    assert member.auth0_id == member_before_update.auth0_id
    assert member.first_name == member_before_update.first_name
    assert member.last_name == member_before_update.last_name
    assert member.age == member_before_update.age
    assert member.birthdate == member_before_update.birthdate
    assert member.city == member_before_update.city
    assert member.membership_expiration == date(2024, 3, 15)
    assert member.membership_expiration != member_before_update.membership_expiration


def test_delete_member_success(client: TestClient, session: Session):
    member_id = 3
    x = session.exec(select(Member).filter(~col(Member.member_checkouts).any())).one()
    response = client.delete(f"/member/{x.id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Member id {member_id} deleted successfully"}
    member = session.get(Member, member_id)
    assert member is None


def test_create_member_missing_field(client: TestClient):
    new_member = {
        "first_name": "Miss",
        "last_name": "Ingfield",
        "age": 10,
        "birthdate": "2014-01-01",
        "city": "New York",
        "membership_expiration": "2024-03-15",
    }
    response = client.post("/member/", json=new_member)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "auth0_id"],
                "msg": "Field required",
                "input": {
                    "first_name": "Miss",
                    "last_name": "Ingfield",
                    "age": 10,
                    "birthdate": "2014-01-01",
                    "city": "New York",
                    "membership_expiration": "2024-03-15",
                },
                "url": "https://errors.pydantic.dev/2.6/v/missing",
            }
        ]
    }


def test_update_nonexistent_member(client: TestClient):
    updated_member_data = {"returned_date": date.today().isoformat()}
    response = client.put("/member/999", json=updated_member_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Member id 999 not found"


def test_delete_nonexistent_member(client: TestClient):
    response = client.delete("/member/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Member id 999 not found"}
