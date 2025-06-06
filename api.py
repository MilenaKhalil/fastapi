from sqlalchemy.ext.asyncio import AsyncSession
from database import BookModel, get_session
from fastapi import APIRouter, Depends
from schema import BookInfoSchema
from role_enum import Role
from auth import require_role, get_current_user
from sqlalchemy import select

book_router = APIRouter(prefix="/books", tags=["Books"])

#books

@book_router.post(
		"/add_book", tags=["Books"],
		summary="добавление книги в базу данных, только админ может это сделать",
		dependencies=[Depends(require_role(Role.ADMIN))]
)
async def add_book_to_db(book: BookInfoSchema, session: AsyncSession = Depends(get_session)):
	new_book = BookModel(
		title=book.title,
		author=book.author,	
	)
	session.add(new_book)
	await session.commit()
	return {"massage": "Книга добавлена"}

@book_router.get("/book_db", tags=["Books"],
				 summary="get books from database",
				 dependencies=[Depends(get_current_user)])
async def get_all_books(session: AsyncSession = Depends(get_session)):
	query = select(BookModel)
	result = await session.execute(query)
	return result.scalars().all()
