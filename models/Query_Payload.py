from typing import List
from pydantic import BaseModel, Field
from models.Response import Response


class RagRequest(BaseModel):
    """The main container for your function's input"""
    question: str = Field(..., example="What are my fitness goals?")
    Session_ID :str
    
class RedisQuery(BaseModel):
    user_id: str = Field(...,min_length=2)
    session_id: str = Field(...,min_length=2)
    query: str = Field(...,min_length=2)
    