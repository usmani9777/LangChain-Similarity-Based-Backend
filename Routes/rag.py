from fastapi import APIRouter

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.get("/info")
async def get_rag_info():
    return {"message": "This is the RAG route"}
