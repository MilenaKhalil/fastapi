from fastapi import APIRouter
# from config import SECRET_KEY
from database import UserModel, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schema import UserInfoSchema
from passlib.context import CryptContext
from sqlalchemy import select
from pydantic import EmailStr
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)

def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
	return pwd_context.verify(plain_pwd, hashed_pwd)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/registration", tags=["Auth"])
async def add_user(user: UserInfoSchema, session: AsyncSession = Depends(get_session)):
	new_user = UserModel(
		email = user.email,
		password = get_password_hash(user.password),
	)
	session.add(new_user)
	await session.commit()
	return {"ok": True}

# @auth_router.post("/login", tags=["Auth"])
# async def login():
# 	return True
	
# @auth_router.get("/login", tags=["Auth"])
# async def protected():
# 	return True

# @auth_router.get("/find_user", tags=["Auth"])
async def get_user_by_email(email: EmailStr, session: AsyncSession = Depends(get_session)) -> bool:
	query = select(UserModel).where(UserModel.email == email)
	result = await session.execute(query)
	user = result.scalar_one_or_none()
	if not user:
		return False
	return True

@auth_router.post("/login", tags=["Auth"])
async def verify_user(email: EmailStr, pl_pwd: str, session: AsyncSession = Depends(get_session)):
	if await get_user_by_email(email, session) is False:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	query = select(UserModel).where(UserModel.email == email)
	result = await session.execute(query)
	user = result.scalar_one()
	if verify_password(pl_pwd, user.password) is False:
		raise HTTPException(status_code=401, detail="Неверный пароль")
	
	return {"ok": True}