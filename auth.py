from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import UserModel, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schema import UserInfoSchema
from role_enum import Role
from passlib.context import CryptContext
from sqlalchemy import select
from pydantic import EmailStr
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")

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
		scope = Role.USER
	)
	session.add(new_user)
	await session.commit()
	return {"message": "Вы зарегистрированы!"}

def require_role(required_scope: Role = Role.USER):
	async def check_permission(current_user: UserModel = Depends(get_current_user)):
		if current_user.scope < required_scope:
			raise HTTPException(
				status_code=403,
				detail=f"Недостаточно прав. Требуется роль {required_scope.name} или выше"
			)
		return current_user
	return check_permission

async def get_current_user(
	token: str = Depends(oauth2_schema),
	session: AsyncSession = Depends(get_session)
) -> UserModel:
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		user_id = payload.get("user_id")
		if user_id is None:
			raise HTTPException(status_code=401, detail="Неверный токен")
		
		if isinstance(user_id, dict):
			user_id = user_id.get("user_id")
			
		# if not isinstance(user_id, int):
		# 	raise HTTPException(status_code=401, detail="Неверный формат токена")
		
		query = select(UserModel).where(UserModel.id == user_id)
		result = await session.execute(query)
		user = result.scalar_one_or_none()
		
		if user is None:
			raise HTTPException(status_code=401, detail="Пользователь не найден")
			
		return user
		
	except JWTError:
		raise HTTPException(status_code=401, detail="Неверный токен")

@auth_router.get("/protected", tags=["Auth"])
async def get_secret_info(current_user: UserModel = Depends(get_current_user)):
	return {
		"secret": "На самом деле книги в этой базе данных не настоящие",
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

@auth_router.post("/login", tags=["Auth"])
async def login(
	login_data: OAuth2PasswordRequestForm = Depends(),
	session: AsyncSession = Depends(get_session)
):
	user_id = await get_user_by_email(login_data.username, session)
	if user_id is False:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	
	query = select(UserModel).where(UserModel.email == login_data.username)
	result = await session.execute(query)
	user = result.scalar_one()
	
	if verify_password(login_data.password, user.password) is False:
		raise HTTPException(status_code=401, detail="Неверный пароль")
	
	token_info = {
		"user_id": user.id,
		"scope": user.scope
	}
	
	access_token = create_access_token(token_info)
	
	return {
		"access_token": access_token,
		"token_type": "bearer"
	}

@auth_router.get("/make_me_admin", tags=["Auth"], dependencies=[Depends(get_current_user)])
async def chenge_scope(user: UserModel = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
	user.scope = Role.ADMIN
	await session.commit()
	return {"message": "Вы стали админом!"}
