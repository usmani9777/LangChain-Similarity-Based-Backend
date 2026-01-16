from pydantic import BaseModel, Field

class Response(BaseModel):
    Status_Code :int = Field(..., description="HTTP Status Code of the response")
    Article_Summary:str = Field(..., description="Summary of the article related to the query")
    Article:str = Field(..., description="Data from article related to the given query")
    Answer:str = Field(..., description="Answer to the query based on the article")