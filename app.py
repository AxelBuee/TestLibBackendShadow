from dotenv import load_dotenv
from fastapi import FastAPI
from utils import get_token
from routers import author, book, checkout, copy, member
from db import create_db_and_tables, delete_db_and_tables, engine
from setup import (
    create_authors_and_books,
    create_members,
    create_copies,
    create_checkouts,
)

load_dotenv()
app = FastAPI(title="Shadow library API")
get_token()


app.include_router(author.router, tags=["Author"])
app.include_router(book.router, tags=["Book"])
app.include_router(book.unsecure_router, tags=["Book"])
app.include_router(copy.router, tags=["Copy"])
app.include_router(checkout.router, tags=["Checkout"])
app.include_router(member.router, tags=["Member"])

# This would be removed in production but is useful for development
# This will reset the database everytime you run the app. Comment as needed.

print("Deleting tables.")
delete_db_and_tables(engine)
print("Creating the tables.")
create_db_and_tables(engine)
print("Inserting basic values.")
create_authors_and_books(engine)
create_members(engine)
create_copies(engine)
create_checkouts(engine)
# if __name__ == "__main__":
