from fastapi import APIRouter, Depends
from database import get_session, UserModel
from schema import UserInfoSchema
from role_enum import Role
from auth import get_password_hash, require_role
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

user_router = APIRouter(prefix="/users", tags=["Users"])

@user_router.post("/registration", tags=["Users"])
async def register(user: UserInfoSchema, session: AsyncSession = Depends(get_session)):
	new_user = UserModel(
		email = user.email,
		password = get_password_hash(user.password),
		scope = Role.USER
	)
	session.add(new_user)
	await session.commit()
	return {"message": "Вы зарегистрированы!"}

@user_router.get("/users_db", tags=["Users"],
				 summary="get all users from database, only admin can do this",
				 dependencies=[Depends(require_role(Role.ADMIN))])
async def get_all_books(session: AsyncSession = Depends(get_session)):
	query = select(UserModel)
	result = await session.execute(query)
	return result.scalars().all()