from fastapi import APIRouter, UploadFile, File, HTTPException,BackgroundTasks
from pathlib import Path
from Services.File_check import get_unique_filename
import shutil
from Services.convert_to_txt import save_text_to_txt
from models.Text_Upload import TextUploadRequest
from Services.Rag import add_data ,process_file_background
import logging

router = APIRouter(prefix="/rag", tags=["RAG"])

logger = logging.getLogger(__name__)


UPLOAD_DIR = Path("Storage")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
Session_ID: str= None

 

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
        logging.info("Convert and add endpoint called")
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
        logging.info("List storage files endpoint called")
        files = get_unique_filename(UPLOAD_DIR, FileName)

        return {"files": files}
    except Exception as e:
        logging.exception("Listing files failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {str(e)}"
        )
        
