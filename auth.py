import jwt
from datetime import datetime, timedelta
from fastapi import APIRouter, Response, Request, Cookie
from config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from database import UserModel, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from schema import UserInfoSchema
from passlib.context import CryptContext
from sqlalchemy import select
from pydantic import EmailStr
from typing import Optional
from datetime import timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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

@auth_router.get("/protected", tags=["Auth"])
async def get_secret_info(access_token: Optional[str] = Cookie(default=None)):
	if not access_token:
		raise HTTPException(status_code=401, detail="Не найден токен авторизации")
	try:
		payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
		user_id = payload.get("user_id")
		if user_id is None:
			raise HTTPException(status_code=401, detail="Неверный токен")
		return {"secret": "This is a secret message"}
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=401, detail="Токен истек")
	except jwt.JWTError:
		raise HTTPException(status_code=401, detail="Неверный формат токена")

def create_access_token(user_id: int):
	to_encode = {"user_id": user_id}
	expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
	to_encode.update({"exp": expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt

# мб прооверять уникальность почты?
async def get_user_by_email(email: EmailStr, session: AsyncSession = Depends(get_session)) -> Optional[int]:
	query = select(UserModel).where(UserModel.email == email)
	result = await session.execute(query)
	user = result.scalar_one_or_none()
	if not user:
		return False
	return user.id

@auth_router.post("/login", tags=["Auth"])
async def login(email: EmailStr, pl_pwd: str, response: Response, session: AsyncSession = Depends(get_session)):
	if await get_user_by_email(email, session) is False:
		raise HTTPException(status_code=404, detail="Пользователь не найден")
	query = select(UserModel).where(UserModel.email == email)
	result = await session.execute(query)
	user = result.scalar_one()
	if verify_password(pl_pwd, user.password) is False:
		raise HTTPException(status_code=401, detail="Неверный пароль")
	access_token = create_access_token(user.id)
	response.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True,
        max_age=60*ACCESS_TOKEN_EXPIRE_MINUTES,
        secure=True,
        samesite="lax"
    )
	return {"message": "Вы успешно вошли в систему"}

@auth_router.get("/logout", tags=["Auth"])
async def logout(response: Response):
	response.delete_cookie("access_token")
	return {"message": "Вы успешно вышли из системы"}