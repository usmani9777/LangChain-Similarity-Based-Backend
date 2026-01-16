# from fastapi import APIRouter, UploadFile, File
# from fastapi.responses import JSONResponse
# from pathlib import Path

# from Services.Rag import Rag_func,add_data,retrival

# router = APIRouter(prefix="/user", tags=["User"])

# UPLOAD_DIR = Path("Storage")
# # UPLOAD_DIR.mkdir(exist_ok=True)  # Ensure folder exists

# @router.get("/info")
# async def get_user_info():
#     return {"message": "This is the user route"}

# @router.post("/Prompting")
# async def prompt_user(Question: str):
#     return {"You sent": Question}

# @router.post("/Prompting_with_rag")
# async def prompt_user(Question: str):
#     return Rag_func(Question)

# @router.get("/Retrival_Check")
# async def Retrival(Question: str):
#     return retrival(Question)

# @router.post("/add_file")
# async def add_file(file: UploadFile = File(...)):
#     # Check file type
#     if not file.filename.endswith(".txt"):
#         return JSONResponse(
#             status_code=400, 
#             content={"error": "Only .txt files are allowed"}
#         )

#     # Save the uploaded file
#     file_path = UPLOAD_DIR / file.filename
#     with open(file_path, "wb") as f:
#         content = await file.read()
#         f.write(content)
#     if not add_data(file.filename):
#         return JSONResponse(
#             status_code=500,
#             content={"error": "Failed to add data to RAG vector store"}
#         )
        

#     # Optional: Here you can call your RAG vector store to add this file
#     # rag.add_data(str(file_path))

#     return {"message": f"File '{file.filename}' uploaded successfully"}




from fastapi import APIRouter, UploadFile, File, HTTPException, Query,BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path

from Services.File_check import get_unique_filename
from models.Response import Response
import shutil
from Services.convert_to_txt import save_text_to_txt
from models.Text_Upload import TextUploadRequest

from Services.Rag import rag_answer, add_data, retrieve_context
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/user", tags=["User"])

UPLOAD_DIR = Path("Storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
    try:
        logging.info("RAG prompt endpoint called", extra={"question": question})
        answer =await rag_answer(question)
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
        results = await retrieve_context(question)
        return {"results": results}
    except Exception as e:
        logging.exception("Retrieval failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Retrieval failed: {str(e)}"
        )
        
async def process_file_background(filename: str):
    success = await add_data(filename)
    if not success:
        # Log instead of raising exception
        logger.error(f"Background ingestion failed for file: {filename}")
            
@router.post("/add-file_withBackground", status_code=201)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are allowed"
        )
    logging.info("File upload with background ingestion called", extra={"filename": file.filename})
    files = get_unique_filename(UPLOAD_DIR, file.filename)
    file_path = UPLOAD_DIR / files

    try:
        # 2. Save file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Run vector DB ingestion in background
        background_tasks.add_task(
            process_file_background,
            str(files)
        )

        return {
            "message": "File uploaded successfully. Indexing in progress.",
            "filename": file.filename
        }

    except Exception as e:
        logging.exception("File upload failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        await file.close()
    
    
    
@router.post("/add-file", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    # 1. Validate file type
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are allowed"
        )
    files = get_unique_filename(UPLOAD_DIR, file.filename)
    file_path = UPLOAD_DIR / files

    try:
        logging.info("File upload called", extra={"filename": file.filename})
        # 2. Save file safely
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Add to vector DB
        success = add_data(str(files))
        if not success:
            raise RuntimeError("Vector DB ingestion failed")

        return {
            "message": "File uploaded and indexed successfully",
            "filename": file.filename
        }

    except Exception as e:
        logging.exception("File upload failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=str(e)
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