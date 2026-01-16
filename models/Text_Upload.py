from pydantic import BaseModel, Field

class TextUploadRequest(BaseModel):
    data: str
    filename: str