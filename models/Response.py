from pydantic import BaseModel, Field

class Response(BaseModel):
    Status_Code :int = Field(..., description="HTTP Status Code of the response")
    Saving: str = Field(..., description="Tell me Facts , Goal or Personal things in the Question or Answer worth Saving")
    # Saving: bool = Field(..., description="is question good or not Check whether the code Question only the question consist some fact , goals , Preference or long term personal context if yes then True else False") 
    Question : str = Field(...,description="Question Asked by User")
    # Article_Summary:str = Field(..., description="Summary of the article related to the query")
    Article:str = Field(..., description="Data from article related to the given query")
    Answer:str = Field(..., description="Answer to the query based on the article")

class Session_stats(BaseModel):
    Session_ID :str
    Answer : Response