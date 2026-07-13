from fastapi import FastAPI
from app.auth.routes import router as auth_router
from app.api.v1.router import v1_router
from app.core.exception_handlers import register_exception_handlers

app = FastAPI()

register_exception_handlers(app)

app.include_router(auth_router)
app.include_router(v1_router)


@app.get("/health")
def healthcheck():
    return {"status": "ok"}
