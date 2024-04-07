from datetime import date
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel

"""
SQLModel is a library for interacting with SQL databases from Python code, with Python
objects. It is designed to be intuitive, easy to use, highly compatible, and robust.
SQLModel is based on Python type annotations, and powered by Pydantic and SQLAlchemy.
Created by the same person who created FastAPI (@tiangolo):
https://sqlmodel.tiangolo.com/
"""

# Since Pydantic models are tricky to declare with circular dependencies when split into
# separate files, I just put all the models in the same file.


class AuthorBookLink(SQLModel, table=True):  # type: ignore
    book_id: Optional[int] = Field(
        default=None, foreign_key="books.id", primary_key=True
    )
    author_id: Optional[int] = Field(
        default=None, foreign_key="authors.id", primary_key=True
    )


# ========= Book =========


class BookBase(SQLModel):
    title: str
    isbn: str = Field(unique=True, nullable=False)
    edition: str
    publication_date: date
    language: str


class Book(BookBase, table=True):  # type: ignore
    __tablename__ = "books"

    id: Optional[int] = Field(default=None, primary_key=True)

    copies: Optional[List["Copy"]] = Relationship(back_populates="book")
    authors: List["Author"] = Relationship(
        back_populates="books", link_model=AuthorBookLink
    )


class BookCreate(BookBase):
    authors_ids: List[int]


class BookRead(BookBase):
    id: int


class BookUpdate(SQLModel):
    title: Optional[str] = None
    isbn: Optional[str] = None
    edition: Optional[str] = None
    publication_date: Optional[date] = None
    language: Optional[str] = None
    authors_ids: Optional[List[int]] = None


class BookReadWithAuthors(BookRead):
    copies: Optional[List["CopyRead"]] = []
    authors: List["AuthorRead"]


# ========= Author =========


class AuthorBase(SQLModel):
    first_name: str
    last_name: str
    date_of_birth: date
    date_of_death: Optional[date] = None
    nationality: str


class Author(AuthorBase, table=True):  # type: ignore
    __tablename__ = "authors"

    id: Optional[int] = Field(default=None, primary_key=True)

    books: List["Book"] = Relationship(
        back_populates="authors", link_model=AuthorBookLink
    )


class AuthorCreate(AuthorBase):
    pass


class AuthorRead(AuthorBase):
    id: int


class AuthorUpdate(SQLModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    nationality: Optional[str] = None


class AuthorReadWithBooks(AuthorRead):
    books: Optional[List["BookRead"]] = []


# ========= Copy =========


class CopyBase(SQLModel):
    barcode: str = Field(unique=True)
    location: str
    is_available: bool
    book_id: int = Field(foreign_key="books.id", nullable=False)


class Copy(CopyBase, table=True):  # type: ignore
    __tablename__ = "copies"
    id: Optional[int] = Field(default=None, primary_key=True)

    book: "Book" = Relationship(back_populates="copies")
    checkouts: Optional[List["Checkout"]] = Relationship(back_populates="copy_item")


class CopyCreate(CopyBase):
    pass


class CopyRead(CopyBase):
    id: int


class CopyUpdate(SQLModel):
    barcode: Optional[str] = None
    location: Optional[str] = None
    is_available: Optional[bool] = None
    book_id: Optional[int] = None


class CopyReadWithCheckouts(CopyRead):
    checkouts: Optional[List["CheckoutRead"]] = []


# ========= Checkout =========


class CheckoutBase(SQLModel):
    checkout_date: date
    expected_return_date: date

    member_id: int = Field(foreign_key="members.id", nullable=False)
    copy_id: int = Field(foreign_key="copies.id", nullable=False)


class Checkout(CheckoutBase, table=True):  # type: ignore
    __tablename__ = "checkouts"

    id: Optional[int] = Field(default=None, primary_key=True)
    returned_date: Optional[date] = None
    current_owner: "Member" = Relationship(back_populates="member_checkouts")
    copy_item: "Copy" = Relationship(back_populates="checkouts")


class CheckoutCreate(CheckoutBase):
    pass


class CheckoutRead(CheckoutBase):
    id: int
    returned_date: Optional[date] = None


class CheckoutUpdate(SQLModel):
    checkout_date: Optional[date] = None
    expected_return_date: Optional[date] = None
    returned_date: Optional[date] = None


class CheckoutReadWithDetails(CheckoutRead):
    current_owner: "MemberRead"
    copy_item: "CopyRead"


# ========= Member =========


class MemberBase(SQLModel):
    auth0_id: str
    first_name: str
    last_name: str
    age: int
    birthdate: date
    city: str
    membership_expiration: date


class Member(MemberBase, table=True):  # type: ignore
    __tablename__ = "members"

    id: Optional[int] = Field(default=None, primary_key=True)

    member_checkouts: Optional[List["Checkout"]] = Relationship(
        back_populates="current_owner"
    )


class MemberCreate(MemberBase):
    pass


class MemberRead(MemberBase):
    id: int


class MemberUpdate(SQLModel):
    auth0_id: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birthdate: Optional[date] = None
    age: Optional[int] = None
    city: Optional[str] = None
    membership_expiration: Optional[date] = None


class MemberReadWithCheckouts(MemberRead):
    member_checkouts: Optional[List["CheckoutRead"]] = []
