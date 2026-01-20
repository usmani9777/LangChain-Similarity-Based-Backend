from fastapi import APIRouter, HTTPException , Query , Depends
from pathlib import Path
from Services.memory_services import get_all_start_methods , get_session_id , Get_ALL , Get_all_keys
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/Session", tags=["Session"])
        

@router.post("/prompt/GetPrompts")
async def GetPrompts(Session_ID : str = Depends(get_session_id)):
    try:
        
        logging.info("Checking Prmpts retrival",)
        Prompts = await get_all_start_methods(Session_ID)
        return Prompts
    except Exception as e:
        logging.exception("RAG processing failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(e)}"
        )
 

@router.post("/prompt/Get_All")
async def GETALL():
    try:
        logging.info("Getting all Prompts of all user Using Get ALl",)
        Prompts = await Get_ALL()
        return Prompts
    except Exception as e:
        logging.exception("RAG processing failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(e)}"
        )
               

@router.post("/prompt/Get_all_keys")
async def GETALL():
    try:
        logging.info("Getting All Keys",)
        Prompts = await Get_all_keys()
        return Prompts
    except Exception as e:
        logging.exception("RAG processing failed", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"RAG processing failed: {str(e)}"
        ) 
        
@router.post("/prompt/Very_Important")
async def GETALL():
    try:
        logging.info("Very Important Route",)
        
        return {'Message':'Mohammed Nayal is Amazing and Awesome Python Developer'}
    except Exception as e:
        logging.exception("Nayal Is Not Awesome", extra={"error": str(e)})
        raise HTTPException(
            status_code=500,
            detail=f"Trust me if baber Azam can have a downfall why not nayal: {str(e)}"
        )        
# async def Get_all_keys():
#     dicts = Memory_store.get_all_keys()
    