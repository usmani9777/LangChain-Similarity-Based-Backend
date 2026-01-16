from fastapi import APIRouter, UploadFile, File, HTTPException, Query,BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path

from Services.File_check import get_unique_filename
from models.Response import Response
import shutil
from Services.convert_to_txt import save_text_to_txt
from models.Text_Upload import TextUploadRequest
from Services.memory_services import add_Prompt, get_all_start_methods,SetSessionID
from Services.Rag import rag_answer, add_data, retrieve_context,process_file_background
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User"])

UPLOAD_DIR = Path("Storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Session_ID: str= None

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
    question: str = Query(..., min_length=3)
):
    global Session_ID
    try:
        if Session_ID == None: Session_ID = SetSessionID()
        logging.info("RAG prompt endpoint called", extra={"question": question})
        Prompts =await get_all_start_methods(Session_ID)
        answer =await rag_answer(question,Prompts)
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
    global Session_ID
    try:
        if Session_ID == None: Session_ID = SetSessionID()
        logging.info("Retrieval endpoint called", extra={"question": question})
        results = await retrieve_context(question,)
        return {"results": results}
    except Exception as e:
        logging.exception("Retrieval failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )
        

@router.post("/add-file_withBackground", status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # ✅ Correct file validation
    if not file.filename.lower().endswith((".txt", ".pdf")):
        raise HTTPException(
            status_code=400,
            detail="Only .txt and .pdf files are allowed"
        )

    logger.info(
        "File upload with background ingestion called",
        extra={"file": file.filename}
    )
    
    files = get_unique_filename(UPLOAD_DIR, file.filename)
    file_path = UPLOAD_DIR / files

    try:
        # Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        
        background_tasks.add_task(
            process_file_background,
            str(file_path)
        )

        return {
            "message": "File uploaded successfully. Indexing in progress.",
            "filename": file.filename
        }

    except Exception as e:
        logger.exception("File upload failed")
        raise HTTPException(
            status_code=500,
            detail="File upload failed"
        )

    finally:
        await file.close()
    

@router.post("/convert-and-add", status_code=201)
async def convert_and_upload(payload: TextUploadRequest):
    try:
        logging.info("Convert and add endpoint called", extra={"filename": payload.filename})
        file_name = get_unique_filename(UPLOAD_DIR, payload.filename)
        txt_path = save_text_to_txt(
            content=payload.data,
            filename=file_name
        )

        if not add_data(str(file_name)):
            raise RuntimeError("Vector DB ingestion failed")

        return {
            "message": "File saved and indexed successfully",
            "filename": file_name,
            "txt_file": txt_path.name
        }

    except ValueError as e:
        logging.exception("Invalid input for text conversion", extra={"error": str(e)})
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logging.exception("Conversion and upload failed", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/Check-Files")
async def list_storage_files(FileName: str):
    try:
        logging.info("List storage files endpoint called", extra={"filename": FileName})
        files = get_unique_filename(UPLOAD_DIR, FileName)

        return {"files": files}
    except Exception as e:
        logging.exception("Listing files failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {str(e)}"
        )
        
        
# async def SetSessionID():
#     """Sets a unique session ID for the RAG store."""
#     import uuid
#     session_id = str(uuid.uuid4())
#     rag_store.set_session_id(session_id)
#     logger.info(f"Session ID set to {session_id}")
#     return session_id

@router.post("/set-session", status_code=200)
async def set_session():
    try:
        global Session_ID
        logging.info("Set session endpoint called")
        Session_ID = await SetSessionID()
        return {"message": "Session ID set successfully"}
    except Exception as e:
        logging.exception("Setting session ID failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set session ID: {str(e)}"
        )

@router.post("/prompt/GetPrompts")
async def GetPrompts():
    try:
        global Session_ID
        logging.info("Checking Prmpts retrival",)
        Prompts = await get_all_start_methods(Session_ID)
        return Prompts
    except Exception as e:
        logging.exception("RAG processing failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(e)}"
        )