from sqlalchemy.ext.asyncio import AsyncSession
from database import BookModel, Base, get_session, engine
from fastapi import HTTPException, APIRouter, Depends
from schema import BookInfoSchema, UserInfoSchema
from sqlalchemy import select
from typing import List
# from books_base import books
from users_base import users

book_router = APIRouter(prefix="/books", tags=["Books"])
user_router = APIRouter(prefix="/users", tags=["Users"])

#books

@book_router.post("/add_book", tags=["Books"], summary="add book to a database")
async def add_book_to_db(book: BookInfoSchema, session: AsyncSession = Depends(get_session)):
	new_book = BookModel(
		title=book.title,
		author=book.author,	
	)
	session.add(new_book)
	await session.commit()
	return {"ok": True}

@book_router.get("/book_db", tags=["Books"], summary="get books from database")
async def get_book_from_db(session: AsyncSession = Depends(get_session)):
	query = select(BookModel)
	result = await session.execute(query)
	return result.scalars().all()

#users

@user_router.post("/users", tags=["Users"], summary="добавить Юзера")
def add_user(new_user: UserInfoSchema):
	users.append(new_user)
	return {"ok": True}

@user_router.get("/users", tags=["Users"], summary="все юзеры")
def get_all_users() -> List[UserInfoSchema]:
	return users

@user_router.post("/create")
async def init_user_table():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)