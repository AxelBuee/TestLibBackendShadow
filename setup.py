from models.models import Book, Author, Member, Copy, Checkout
from sqlmodel import Session, select
from datetime import date


def create_authors_and_books(engine):
    with Session(engine) as session:
        g_orwell = Author(
            first_name="George",
            last_name="Orwell",
            nationality="English",
            date_of_birth=date(1903, 6, 25),
        )
        a_huxley = Author(
            first_name="Aldous",
            last_name="Huxley",
            nationality="English",
            date_of_birth=date(1894, 7, 26),
        )
        deadpond = Book(
            title="Deadpond",
            isbn="000-0000000000",
            edition="First edition",
            publication_date=date(2018, 1, 1),
            language="English",
            authors=[g_orwell, a_huxley],
        )
        rusty_man = Book(
            title="Hero Rusty",
            isbn="000-0000000001",
            edition="Gallimard",
            publication_date=date(2018, 1, 1),
            language="English",
            teams=[a_huxley],
        )
        lonely_book = Book(
            title="Lonly book",
            isbn="000-0000000002",
            edition="Gallimard",
            publication_date=date(2018, 1, 1),
            language="English",
            teams=[g_orwell],
        )

        session.add(deadpond)
        session.add(rusty_man)
        session.add(lonely_book)
        session.commit()

        session.refresh(deadpond)
        session.refresh(rusty_man)
        session.refresh(lonely_book)


def create_members(engine):
    with Session(engine) as session:
        john = Member(
            auth0_id="a012f_ab23f_1234f",
            first_name="John",
            last_name="Doe",
            age=34,
            birthdate=date(1990, 1, 1),
            city="New York",
            membership_expiration=date(2022, 1, 1),
        )
        jane = Member(
            auth0_id="da33b_1234f_c0e3e",
            first_name="Jane",
            last_name="Doe",
            age=10,
            birthdate=date(2014, 1, 1),
            city="New York",
            membership_expiration=date(2025, 1, 1),
        )
        session.add(john)
        session.add(jane)
        session.commit()


def create_copies(engine):
    with Session(engine) as session:
        deadpond = session.exec(select(Book).where(Book.title == "Deadpond")).one()
        rusty_man = session.exec(select(Book).where(Book.title == "Hero Rusty")).one()
        deadpond_copy = Copy(
            barcode="0100101010",
            location="Shelf 1",
            is_available=True,
            book_id=deadpond.id,
            book=deadpond,
        )
        rusty_man_copy = Copy(
            barcode="1100101011",
            location="Shelf 40",
            is_available=False,
            book_id=rusty_man.id,
            book=rusty_man,
        )
        lonely_copy = Copy(
            barcode="1100100000",
            location="Shelf 40",
            is_available=False,
            book_id=rusty_man.id,
            book=rusty_man,
        )
        session.add(deadpond_copy)
        session.add(rusty_man_copy)
        session.add(lonely_copy)
        session.commit()

        session.refresh(deadpond_copy)
        session.refresh(rusty_man_copy)
        session.refresh(lonely_copy)


def create_checkouts(engine):
    with Session(engine) as session:
        john = session.exec(select(Member).where(Member.first_name == "John")).one()
        jane = session.exec(select(Member).where(Member.first_name == "Jane")).one()

        copy_1 = session.exec(select(Copy).where(Copy.barcode == "0100101010")).one()
        copy_2 = session.exec(select(Copy).where(Copy.barcode == "1100101011")).one()
        checkout_1 = Checkout(
            checkout_date=date(2021, 1, 1),
            expected_return_date=date(2021, 1, 15),
            returned_date=date(2021, 1, 10),
            member_id=john.id,
            copy_id=copy_1.id,
            current_owner=john,
            copy_item=copy_1,
        )
        checkout_2 = Checkout(
            checkout_date=date(2024, 3, 10),
            expected_return_date=date(2024, 3, 15),
            member_id=jane.id,
            copy_id=copy_2.id,
            current_owner=jane,
            copy_item=copy_2,
        )
        session.add(checkout_1)
        session.add(checkout_2)
        session.commit()
