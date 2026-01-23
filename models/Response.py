from pydantic import BaseModel, Field
from typing import Literal  
MemoryType = Literal["Personal", "Goal", "Fact","None"]
class Response(BaseModel):
    Status_Code :int = Field(..., description="HTTP Status Code of the response")
    Saving: MemoryType = Field(
        ...,
        description=(
            "Classify long-term memory. "
            "FACT: Names/Identity (e.g., 'My name is Nayal'); "
            "PERSONAL: Work/Likes (e.g., 'Nayal works at Voltmatic', 'I like dogs'); "
            "GOAL: Future plans (e.g., 'I want to learn AI'); "
            "None: General chat or if its a Question (e.g 'What is Volmatica' , 'Who is Nayal')."
        )
    )
    # Saving: str = Field(...,description="Classify whether the question or answer contains long-term memory. Must be one of: 'Personal', 'Goal','Fact' or 'None'")
    Question : str = Field(...,description="Question Asked by User")
    # Article_Summary:str = Field(..., description="Summary of the article related to the query")
    Article:str = Field(..., description="Data from article related to the given query")
    Answer:str = Field(..., description="Answer to the query based on the Data you are Provided")

class Session_stats(BaseModel):
    Session_ID :str
    Answer : Response