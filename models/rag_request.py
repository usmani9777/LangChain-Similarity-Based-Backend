from pydantic import BaseModel, Field

class RAGRequest_Endpoint(BaseModel):
    question: str = Field(..., min_length=3, description="User question")
    user_id: str = Field(..., min_length=3, description="User identifier")
