from typing import List
from models.models import (
    Book,
    Copy,
    CopyBase,
    CopyCreate,
    CopyRead,
    CopyUpdate,
    CopyReadWithCheckouts,
)
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select
from db import get_db
from utils import VerifyToken

auth = VerifyToken()
router = APIRouter(dependencies=[Security(auth.verify, scopes=['write:author'])])


@router.get("/copies/", response_model=List[CopyRead])
async def get_all_copys(session: Session = Depends(get_db)):
    all_copys = session.exec(select(Copy)).all()
    return all_copys


@router.get("/copy/{copy_id}", response_model=CopyReadWithCheckouts)
async def get_copy(copy_id: int, session: Session = Depends(get_db)):
    db_copy = session.get(Copy, copy_id)
    if not db_copy:
        raise HTTPException(status_code=404, detail=f"Copy id {copy_id} not found")
    return db_copy


def _get_book(session: Session, book_id: int):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail=f"Book id {book_id} not found")
    return book


@router.post("/copy/", response_model=CopyRead)
async def create_copy(copy: CopyCreate, session: Session = Depends(get_db)):
    book = _get_book(session, copy.book_id)
    db_copy = Copy.model_validate(copy)
    db_copy.book = book
    session.add(db_copy)
    session.commit()
    session.refresh(db_copy)
    return db_copy


@router.put("/copy/{copy_id}", response_model=CopyRead)
async def update_copy(
    copy_id: int, copy: CopyUpdate, session: Session = Depends(get_db)
):
    db_copy = session.get(Copy, copy_id)
    if not db_copy:
        raise HTTPException(status_code=404, detail=f"Copy id {copy_id} not found")
    copy_data = copy.model_dump(exclude_unset=True)
    for key, value in copy_data.items():
        setattr(db_copy, key, value)
    session.add(db_copy)
    session.commit()
    session.refresh(db_copy)
    return db_copy


@router.delete("/copy/{copy_id}", response_model=dict)
async def delete_copy(copy_id: int, session: Session = Depends(get_db)):
    db_copy = session.get(Copy, copy_id)
    if not db_copy:
        raise HTTPException(status_code=404, detail=f"Copy id {copy_id} not found")
    session.delete(db_copy)
    session.commit()
    return {"message": f"Copy id {db_copy.id} deleted successfully"}
