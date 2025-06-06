import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Response, Form
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import UserModel, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schema import UserInfoSchema
from passlib.context import CryptContext
from sqlalchemy import select
from pydantic import EmailStr, BaseModel
from typing import Optional, Union
from datetime import timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_password_hash(password: str) -> str:
	return pwd_context.hash(password)

def verify_password(plain_pwd: str, hashed_pwd: str) -> bool:
	return pwd_context.verify(plain_pwd, hashed_pwd)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

@auth_router.post("/registration", tags=["Auth"])
async def register(user: UserInfoSchema, session: AsyncSession = Depends(get_session)):
	new_user = UserModel(
		email = user.email,
		password = get_password_hash(user.password),
	)
	session.add(new_user)
	await session.commit()
	return {"ok": True}

async def get_current_user(
	token: str = Depends(oauth2_schema),
	session: AsyncSession = Depends(get_session)
) -> UserModel:
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		user_id = payload.get("user_id")
		if user_id is None:
			raise HTTPException(status_code=401, detail="Неверный токен")
		
		query = select(UserModel).where(UserModel.id == user_id)
		result = await session.execute(query)
		user = result.scalar_one_or_none()
		
		if user is None:
			raise HTTPException(status_code=401, detail="Пользователь не найден")
			
		return user
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail="Токен истек")
	except jwt.JWTError:
		raise HTTPException(status_code=401, detail="Неверный формат токена")

@auth_router.get("/protected", tags=["Auth"])
async def get_secret_info(current_user: UserModel = Depends(get_current_user)):
	return {
		"secret": "This is a secret message",
		"user_email": current_user.email
	}

def create_access_token(user_id: int):
	to_encode = {"user_id": user_id}
	expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt

# мб прооверять уникальность почты?
async def get_user_by_email(email: EmailStr, session: AsyncSession) -> Optional[int]:
	query = select(UserModel).where(UserModel.email == email)
	result = await session.execute(query)
	user = result.scalar_one_or_none()
	if not user:
		return False
	return user.id

class LoginSchema(BaseModel):
	email: EmailStr
	password: str

@auth_router.post("/token", tags=["Auth"])
async def login_for_access_token(
	form_data: OAuth2PasswordRequestForm = Depends(),
	session: AsyncSession = Depends(get_session)
):
	user_id = await get_user_by_email(form_data.username, session)
	if user_id is False:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	
	query = select(UserModel).where(UserModel.email == form_data.username)
	result = await session.execute(query)
	user = result.scalar_one()
	
	if verify_password(form_data.password, user.password) is False:
		raise HTTPException(
			status_code=401,
			detail="Неверный пароль",
			headers={"WWW-Authenticate": "Bearer"},
		)
	
	access_token = create_access_token(user.id)
	return {
		"access_token": access_token,
		"token_type": "bearer"
	}

@auth_router.post("/login", tags=["Auth"])
async def login(
	login_data: LoginSchema,
	session: AsyncSession = Depends(get_session)
):
	user_id = await get_user_by_email(login_data.email, session)
	if user_id is False:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	
	query = select(UserModel).where(UserModel.email == login_data.email)
	result = await session.execute(query)
	user = result.scalar_one()
	
	if verify_password(login_data.password, user.password) is False:
		raise HTTPException(status_code=401, detail="Неверный пароль")
	
	access_token = create_access_token(user.id)
	
	return {
		"access_token": access_token,
		"token_type": "bearer"
	}

@auth_router.get("/logout", tags=["Auth"])
async def logout(response: Response):
	response.delete_cookie("tokenUrl")
	return {"message": "Вы успешно вышли из системы"}