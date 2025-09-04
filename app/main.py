from fastapi import FastAPI
from app.routers import recommend,swipe, product, user

app = FastAPI(title="Thriftko API")

app.include_router(recommend.router)
app.include_router(swipe.router)
app.include_router(product.router)  
app.include_router(user.router)

@app.get("/")
def root():
    return {"message": "Welcome to Thriftko API!"}