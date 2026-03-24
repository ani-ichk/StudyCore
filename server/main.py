import uvicorn
from fastapi import FastAPI

from core.database import init_db
from api import router as api_router
from core.config import HOST_FAST_API, PORT_FAST_API

app = FastAPI(title="StudyCore Campus API")
app.include_router(api_router)


@app.get("/")
def read_root():
    return {
        "docs": "/docs",
        "api_v1": "/api/v1",
    }


if __name__ == "__main__":
    init_db()
    uvicorn.run(
        "main:app", 
        reload=True, 
        host=HOST_FAST_API, 
        port=PORT_FAST_API
    )