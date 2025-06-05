# import uvicorn
from fastapi import FastAPI
from api import book_router, user_router
from auth import auth_router

app = FastAPI()

app.include_router(book_router)
app.include_router(user_router)
app.include_router(auth_router)

#sudo kill -9 

# if __name__ == "__main__":
# 	uvicorn.run("main:app", port=8003, reload=True)