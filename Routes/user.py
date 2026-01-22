from fastapi import APIRouter, BackgroundTasks, HTTPException, Query,Depends
from models.Response import Response
from Services.memory_services import add_Prompt,get_session_id
from Services.Rag import rag_answer, retrieve_context
import logging
from models.Query_Payload import RagRequest

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
    background_tasks: BackgroundTasks,
    question: str = Query(..., min_length=3),
    Session_ID: str = Depends(get_session_id),
    
):
    try:
        logging.info("RAG prompt endpoint called", extra={"question": question})
        Request = RagRequest(question= question, Session_ID=Session_ID)
        answer = await rag_answer(Request)
        logger.info(f"Answer given by the rag {answer.Saving}")
        # await add_Prompt(answer.model_dump(),Session_ID)
        logging.info(f"The User asked the Question and Answer was {answer}")
        background_tasks.add_task(
                add_Prompt,
                answer.model_dump(),
                Session_ID)
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
