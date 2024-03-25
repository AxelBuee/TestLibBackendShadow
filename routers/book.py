from typing import List
from models.models import (
    Book,
    BookCreate,
    BookRead,
    BookUpdate,
    BookReadWithAuthors,
    Author,
)
from fastapi import APIRouter, Depends, HTTPException, Security
from sqlmodel import Session, select, extract
from db import get_db
from utils import VerifyToken

auth = VerifyToken()
router = APIRouter(dependencies=[Security(auth.verify, scopes=['write:author'])])


@router.get("/books/", response_model=List[BookRead])
async def get_all_books(session: Session = Depends(get_db)):
    all_books = session.exec(select(Book)).all()
    return all_books


@router.get("/book/{book_id}", response_model=BookReadWithAuthors)
async def get_book(book_id: int, session: Session = Depends(get_db)):
    db_book = session.get(Book, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail=f"Book id {book_id} not found")
    return db_book


def _get_authors(session: Session, authors_ids: List[int]):
    authors = session.exec(select(Author).filter(Author.id.in_(authors_ids))).all()
    existing_authors_ids = {author.id for author in authors}
    missing_authors_ids = set(authors_ids) - existing_authors_ids
    if missing_authors_ids:
        raise HTTPException(
            status_code=404, detail=f"No author with ids {missing_authors_ids} found"
        )
    return authors


# I think it can be a good idea to force the user to provide the authors when creating a book
# since a book always has at least one author.
@router.post("/book/", response_model=BookRead)
async def create_book(book: BookCreate, session: Session = Depends(get_db)):
    authors = _get_authors(session, book.authors_ids)
    db_book = Book.model_validate(book)
    db_book.authors = authors
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@router.put("/book/{book_id}", response_model=BookRead)
async def update_book(
    book_id: int, book: BookUpdate, session: Session = Depends(get_db)
):
    db_book = session.get(Book, book_id)
    if db_book is None:
        raise HTTPException(status_code=404, detail=f"Book id {book_id} not found")
    if book.authors_ids:
        authors = _get_authors(session, book.authors_ids)
        db_book.authors = authors
    book_data = book.model_dump(exclude_unset=True, exclude={"authors_ids"})
    for key, value in book_data.items():
        setattr(db_book, key, value)
    session.add(db_book)
    session.commit()
    session.refresh(db_book)
    return db_book


@router.delete("/book/{book_id}", response_model=dict)
async def delete_book(book_id: int, session: Session = Depends(get_db)):
    db_book = session.get(Book, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail=f"Book id {book_id} not found")
    session.delete(db_book)
    session.commit()
    return {"message": f"Book id {db_book.id} deleted successfully"}


@router.get("/books/search", response_model=List[BookRead])
async def search_books(
    title: str = None,
    publication_year: int = None,
    isbn: str = None,
    language: str = None,
    author_name: str = None,
    session: Session = Depends(get_db),
):
    query = select(Book)
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if publication_year:
        query = query.filter(extract("year", Book.publication_date) == publication_year)
    if isbn:
        query = query.filter(Book.isbn == isbn)
    if language:
        query = query.filter(Book.language.ilike(f"%{language}%"))
    if author_name:
        query = query.join(Book.authors).filter(
            (Author.first_name.ilike(f"%{author_name}%"))
            | (Author.last_name.ilike(f"%{author_name}%"))
        )
    books = session.exec(query).all()
    return books
