from fastapi import FastAPI
from app.routers import user, product, swipe, recommend  

app = FastAPI()

app.include_router(user.router)
app.include_router(product.router)
app.include_router(swipe.router)
app.include_router(recommend.router) 

@app.get("/")
def read_root():
    return {"message": "Welcome to Thriftko API!"}
