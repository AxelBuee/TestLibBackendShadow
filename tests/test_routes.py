# import pytest
# from fastapi.testclient import TestClient
# from app import app
# from setup import (
#     create_authors_and_books,
#     create_members,
#     create_checkouts,
#     create_copies,
# )
# from db import get_db
# from sqlmodel import create_engine, Session, SQLModel, select
# from models.models import MemberCreate, MemberUpdate, Member, Book, Copy
# import json
# import copy as cp
# from datetime import date, timedelta

# SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )
# TestingSessionLocal = Session(autocommit=False, autoflush=False, bind=engine)


# @pytest.fixture()
# def session():
#     SQLModel.metadata.drop_all(bind=engine)
#     SQLModel.metadata.create_all(bind=engine)
#     create_authors_and_books(engine)
#     create_members(engine)
#     create_copies(engine)
#     create_checkouts(engine)

#     db = TestingSessionLocal

#     try:
#         yield db
#     finally:
#         db.close()


# @pytest.fixture()
# def client(session):

#     # Dependency override
#     def override_get_db():
#         try:
#             yield session
#         finally:
#             session.close()

#     app.dependency_overrides[get_db] = override_get_db

#     yield TestClient(app)

