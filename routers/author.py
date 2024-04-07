from typing import List

from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select

from db import get_db
from models.models import (
    Author,
    AuthorCreate,
    AuthorRead,
    AuthorReadWithBooks,
    AuthorUpdate,
)
from utils import VerifyToken

auth = VerifyToken()

router = APIRouter(dependencies=[Security(auth.verify, scopes=["admin"])])

# Example of a route that requires a valid access token
# @router.get("/api/private")
# def private(auth_result: str = Security(auth.verify)):
#     """A valid access token is required to access this route"""
#     return auth_result

# Example of a route that requires a valid access token and an appropriate scope
# # , dependencies=[Security(auth.verify, scopes=['write:author'])]
# @router.get("/api/private-scoped")
# def private_scoped(auth_result: str = Security(auth.verify, scopes=["write:author"])):
#     """A valid access token and an appropriate scope are required to access
#     this route
#     """
#     return auth_result


@router.get("/authors/", response_model=List[AuthorRead])
async def get_all_authors(session: Session = Depends(get_db)):
    all_authors = session.exec(select(Author)).all()
    return all_authors


@router.get("/author/{author_id}", response_model=AuthorReadWithBooks)
async def get_author(author_id: int, session: Session = Depends(get_db)):
    db_author = session.get(Author, author_id)
    if not db_author:
        raise HTTPException(status_code=404, detail=f"Author id {author_id} not found")
    return db_author


@router.post("/author/", response_model=AuthorRead)
async def create_author(author: AuthorCreate, session: Session = Depends(get_db)):
    db_author = Author.model_validate(author)
    session.add(db_author)
    session.commit()
    session.refresh(db_author)
    return db_author


@router.put("/author/{author_id}", response_model=AuthorRead)
async def update_author(
    author_id: int, author: AuthorUpdate, session: Session = Depends(get_db)
):
    db_author = session.get(Author, author_id)
    if not db_author:
        raise HTTPException(status_code=404, detail=f"Author id {author_id} not found")
    author_data = author.model_dump(exclude_unset=True)
    for key, value in author_data.items():
        setattr(db_author, key, value)
    session.add(db_author)
    session.commit()
    session.refresh(db_author)
    return db_author


@router.delete("/author/{author_id}", response_model=dict)
async def delete_author(author_id: int, session: Session = Depends(get_db)):
    db_author = session.get(Author, author_id)
    if not db_author:
        raise HTTPException(status_code=404, detail=f"Author id {author_id} not found")
    session.delete(db_author)
    session.commit()
    return {"message": f"Author id {db_author.id} deleted successfully"}
