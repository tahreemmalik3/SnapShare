from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
from app.routes import users, photos, comments, ratings

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SnapShare API",
    description="""
## SnapShare — Cloud Native Photo Sharing Platform

A scalable, cloud-native photo sharing platform built with:
- **FastAPI** — high-performance REST API
- **PostgreSQL** — relational database via SQLAlchemy
- **Azure Blob Storage** — scalable object storage for images
- **Azure Computer Vision** — AI-powered auto-tagging
- **Azure Text Analytics** — sentiment analysis on comments
- **JWT Authentication** — role-based access (Creator / Consumer)

### Roles
- **Creator**: Can upload photos with metadata (title, caption, location, people)
- **Consumer**: Can browse, search, comment, and rate photos
    """,
    version="1.0.0",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
# Allow frontend (Static Web App or localhost) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # In production: set to your Static Web App URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── ROUTES ──────────────────────────────────────────────────────────────────
app.include_router(users.router)
app.include_router(photos.router)
app.include_router(comments.router)
app.include_router(ratings.router)

# ─── ROOT ────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "message": "SnapShare API Running Successfully",
        "version": "1.0.0",
        "docs":    "/docs",
        "status":  "healthy"
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
