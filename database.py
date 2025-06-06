from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from role_enum import Role

class Base(DeclarativeBase):
	pass

class BookModel(Base):
	__tablename__ = "Books"
	id: Mapped[int] = mapped_column(primary_key=True)
	title: Mapped[str] = mapped_column()
	author: Mapped[str] = mapped_column()
	# nice_cover = Mapped[bool] 
	
class UserModel(Base):
	__tablename__ = "Users"
	id: Mapped[int] = mapped_column(primary_key=True)
	email: Mapped[str] = mapped_column()
	password: Mapped[str] = mapped_column()
	scope: Mapped[Role] = mapped_column(default=Role.USER)

engine = create_async_engine('sqlite+aiosqlite:///data.db')

new_session = async_sessionmaker(engine, expire_on_commit=False)

async def get_session():
	async with new_session() as session:
		yield session
		
async def init_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)