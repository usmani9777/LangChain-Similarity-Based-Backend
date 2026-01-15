from fastapi import APIRouter

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/info")
async def get_user_info():
    return {"message": "This is the user route"}
