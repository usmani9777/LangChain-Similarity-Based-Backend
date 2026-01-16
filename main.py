from fastapi import FastAPI
from Routes.user import router as user_router
from Routes.rag import router as rag_router
from Services.logging_config import setup_logging

setup_logging()
import logging

logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(user_router)
app.include_router(rag_router)
# app.on_event("startup")(logger.info("Application startup complete."))

@app.get("/")
async def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app="main:app", host="0.0.0.0", port=8000, reload=True)