from typing import List
from models.models import (
    Member,
    MemberCreate,
    MemberRead,
    MemberUpdate,
    MemberReadWithCheckouts,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_db

router = APIRouter()


@router.get("/members/", response_model=List[MemberRead])
async def get_all_members(session: Session = Depends(get_db)):
    all_members = session.exec(select(Member)).all()
    return all_members


@router.get("/member/{member_id}", response_model=MemberReadWithCheckouts)
async def get_member(member_id: int, session: Session = Depends(get_db)):
    db_member = session.get(Member, member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    return db_member


@router.post("/member/", response_model=MemberRead)
async def create_member(member: MemberCreate, session: Session = Depends(get_db)):
    db_member = Member.model_validate(member)
    session.add(db_member)
    session.commit()
    session.refresh(db_member)
    return db_member


@router.put("/member/{member_id}", response_model=MemberRead)
async def update_member(
    member_id: int, member: MemberUpdate, session: Session = Depends(get_db)
):
    db_member = session.get(Member, member_id)
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    member_data = member.model_dump(exclude_unset=True)
    for key, value in member_data.items():
        setattr(db_member, key, value)
    session.add(db_member)
    session.commit()
    session.refresh(db_member)
    return db_member


@router.delete("/member/{member_id}", response_model=MemberRead)
async def delete_member(member_id: int, session: Session = Depends(get_db)):
    db_member = session.get(Member, member_id)
    if db_member.member_checkouts:
        raise HTTPException(
            status_code=404,
            detail="Member has checkouts. Please consider deactivating him instead.",
        )
    if not db_member:
        raise HTTPException(status_code=404, detail="Member not found")
    session.delete(db_member)
    session.commit()
    return db_member
