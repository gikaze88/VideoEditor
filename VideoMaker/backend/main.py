"""
VideoMaker — FastAPI backend
Port: 8001
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import jobs as jobs_router
from .routers import assets as assets_router
from .routers import sources as sources_router
from .config import OUTPUTS_DIR, PROJECT_ROOT

app = FastAPI(title="VideoMaker API", version="1.0.0")

# 1. CORS — autoriser le frontend dev (5174) et la version buildée
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Init base de données au démarrage
@app.on_event("startup")
def on_startup():
    init_db()

# 3. Routers API (AVANT les static files, sinon 404)
app.include_router(jobs_router.router)
app.include_router(assets_router.router)
app.include_router(sources_router.router)

# 4. Servir les outputs (vidéos générées)
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# 5. Servir le frontend buildé — TOUJOURS EN DERNIER
frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
