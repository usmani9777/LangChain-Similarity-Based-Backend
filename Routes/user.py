from fastapi import APIRouter, UploadFile, File, HTTPException, Query,BackgroundTasks,Depends
from models.Response import Response

from Services.memory_services import add_Prompt, get_all_start_methods,get_session_id
from Services.Rag import rag_answer, retrieve_context
import logging
from Services.LongTermMemory import process_query
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User"])



@router.get("/info")
async def get_user_info():
    logging.info("User info endpoint called")
    return {"message": "This is the user route"}

@router.post("/prompt")
async def prompt_user(
    question: str = Query(..., min_length=3, description="User question")
):
    logging.info("Prompt endpoint called", extra={"question": question})
    return {"question": question}


@router.post("/prompt/rag" , response_model=Response)
async def prompt_with_rag(
    question: str = Query(..., min_length=3),
    Session_ID: str = Depends(get_session_id)
):
    try:
        
        logging.info("RAG prompt endpoint called", extra={"question": question})
        Prompts = await get_all_start_methods(Session_ID)
        memories = process_query(Session_ID, Session_ID, question)
        answer = await rag_answer(question,Prompts,memories)
        logger.info(f"Answer given by the rag {answer}")
        await add_Prompt(answer.model_dump(),Session_ID)
        return answer
            
    except Exception as e:
        logging.exception("RAG processing failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(e)}"
        )

@router.get("/retrieval")
async def retrieval_check(
    question: str = Query(..., min_length=3)
):
    try:
        logging.info("Retrieval endpoint called", extra={"question": question})
        results = await retrieve_context(question,)
        return {"results": results}
    except Exception as e:
        logging.exception("Retrieval failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )
