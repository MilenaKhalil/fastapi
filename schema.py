from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional

class UserInfoSchema(BaseModel):
	email: EmailStr
	password: str
	# bio: Optional[str] = Field(max_length=1000)
	# age: Optional[int] = Field(ge=0, le=122)
	# model_config = ConfigDict(extra='forbid') # нельзя добавить доп инфо
	
class UserCompromatSchema(UserInfoSchema):
	favourite_cringe_series: Optional[str]
	model_config = ConfigDict(extra='allow')
	
class BookInfoSchema(BaseModel):
	title: str
	author: str
	nice_cover: Optional[bool]
	
