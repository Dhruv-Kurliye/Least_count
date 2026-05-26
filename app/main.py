from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import Base, engine

from app.routes.auth_routes import router as auth_router
from app.routes.match_routes import router as match_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_router)
app.include_router(match_router)