from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import PROJECT_NAME, VERSION, CORS_ORIGINS
from .database import engine, Base
from .routers import halls, exhibits, characters, routes, hotspots, sessions, interactions, events, stats, export

Base.metadata.create_all(bind=engine)

app = FastAPI(title=PROJECT_NAME, version=VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(halls.router)
app.include_router(exhibits.router)
app.include_router(characters.router)
app.include_router(routes.router)
app.include_router(hotspots.router)
app.include_router(sessions.router)
app.include_router(interactions.router)
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(export.router)


@app.get("/")
def root():
    return {"project": PROJECT_NAME, "version": VERSION}


@app.get("/health")
def health():
    return {"status": "ok"}
