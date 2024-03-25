from typing import List
from models.models import (
    Checkout,
    CheckoutCreate,
    CheckoutRead,
    CheckoutUpdate,
    CheckoutReadWithDetails,
    Copy,
    Member,
)
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select
from db import get_db
from datetime import date
from utils import VerifyToken


auth = VerifyToken()
router = APIRouter(dependencies=[Security(auth.verify, scopes=['write:author'])])


@router.get("/checkouts/", response_model=List[CheckoutRead])
async def get_all_checkouts(session: Session = Depends(get_db)):
    all_checkouts = session.exec(select(Checkout)).all()
    return all_checkouts


@router.get("/checkout/{checkout_id}", response_model=CheckoutReadWithDetails)
async def get_checkout(checkout_id: int, session: Session = Depends(get_db)):
    db_checkout = session.get(Checkout, checkout_id)
    if not db_checkout:
        raise HTTPException(
            status_code=404, detail=f"Checkout id {checkout_id} not found"
        )
    return db_checkout


@router.post("/checkout/", response_model=CheckoutRead)
async def create_checkout(checkout: CheckoutCreate, session: Session = Depends(get_db)):
    copy_item = session.get(Copy, checkout.copy_id)
    if not copy_item:
        raise HTTPException(
            status_code=404, detail=f"Copy id {checkout.copy_id} not found"
        )
    if not copy_item.is_available:
        raise HTTPException(
            status_code=404, detail=f"Copy id {checkout.copy_id} is not available"
        )
    member = session.get(Member, checkout.member_id)
    if not member:
        raise HTTPException(
            status_code=404, detail=f"Member id {checkout.member_id} not found"
        )
    elif member.membership_expiration < date.today():
        raise HTTPException(
            status_code=404,
            detail=f"Member id {checkout.member_id} membership expired",
        )
    db_checkout = Checkout.model_validate(checkout)
    copy_item.is_available = False
    db_checkout.copy_item = copy_item
    db_checkout.current_owner = member
    session.add(db_checkout)
    session.commit()
    session.refresh(db_checkout)
    return db_checkout


@router.put("/checkout/{checkout_id}", response_model=CheckoutRead)
async def update_checkout(
    checkout_id: int, checkout: CheckoutUpdate, session: Session = Depends(get_db)
):
    db_checkout = session.get(Checkout, checkout_id)
    if not db_checkout:
        raise HTTPException(
            status_code=404, detail=f"Checkout id {checkout_id} not found"
        )
    checkout_data = checkout.model_dump(exclude_unset=True)
    for key, value in checkout_data.items():
        setattr(db_checkout, key, value)
    if checkout.returned_date <= date.today():
        db_checkout.copy_item.is_available = True
    session.add(db_checkout)
    session.commit()
    session.refresh(db_checkout)
    return db_checkout


@router.delete("/checkout/{checkout_id}", response_model=dict)
async def delete_checkout(checkout_id: int, session: Session = Depends(get_db)):
    db_checkout = session.get(Checkout, checkout_id)
    if not db_checkout:
        raise HTTPException(
            status_code=404, detail=f"Checkout id {checkout_id} not found"
        )
    if not db_checkout.returned_date:
        raise HTTPException(
            status_code=404,
            detail=f"Checkout id {checkout_id} is not returned. Please make sure the book was returned before deleting the checkout",
        )
    session.delete(db_checkout)
    session.commit()
    return {"message": f"Checkout id {db_checkout.id} deleted successfully"}
