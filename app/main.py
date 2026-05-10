from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.routes import users
from app.routes.photos_new import router as photos_router
from app.routes.comments_new import router as comments_router
from app.routes.ratings_new import router as ratings_router
from app.db import init_cosmos

@app.on_event("startup")
def startup():
    init_cosmos()

print("APP STARTING SUCCESSFULLY")
app = FastAPI(title="SnapShare API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
os.makedirs("static/uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(users.router)
app.include_router(photos_router)
app.include_router(comments_router)
app.include_router(ratings_router)

@app.get("/")
def root():
    return {"message": "SnapShare API Running Successfully", "database": "Azure Cosmos DB"}

@app.get("/health")
def health():
    return {"status": "ok"}
