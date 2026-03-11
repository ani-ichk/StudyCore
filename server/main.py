import uvicorn
from fastapi import FastAPI
from server.api import router as api_router
from server.data.db.seed import init_db

app = FastAPI(title="Campus API")
app.include_router(api_router)


@app.on_event("startup")
def on_startup():
    """Инициализируем БД при старте сервера"""
    init_db()


@app.get("/")
def read_root():
    return {
        "docs": "/docs",
        "api_v1": "/api/v1",
    }


if __name__ == "__main__":
    uvicorn.run("server.main:app", reload=True)