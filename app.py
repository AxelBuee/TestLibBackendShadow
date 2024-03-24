from dotenv import load_dotenv
from fastapi import FastAPI
from utils import get_token
from routers import author, book, checkout, copy, member, protected
from db import create_db_and_tables, delete_db_and_tables, engine
from setup import (
    create_authors_and_books,
    create_members,
    create_copies,
    create_checkouts,
)

load_dotenv()
app = FastAPI(title="OurLove API")
get_token()


app.include_router(author.router, tags=["Author"])
app.include_router(book.router, tags=["Book"])
app.include_router(copy.router, tags=["Copy"])
app.include_router(checkout.router, tags=["Checkout"])
app.include_router(member.router, tags=["Member"])


@app.get("/ping")
def pong():
    return {"ping": "pong!"}


# app.include_router(protected.router, tags=["Protected"])

if __name__ == "__main__":
    delete_db_and_tables(engine)
    create_db_and_tables(engine)
    create_authors_and_books(engine)
    create_members(engine)
    create_copies(engine)
    create_checkouts(engine)
