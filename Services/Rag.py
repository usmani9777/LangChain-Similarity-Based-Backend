from typing import List
from models.Response import Response
from langchain_core.output_parsers import PydanticOutputParser
from core.prompt import prompt_rag
from core.dependecies import get_llm,initialize_vector_store
from logging import getLogger

logger = getLogger(__name__)
parser = PydanticOutputParser(pydantic_object=Response)
rag_chain = prompt_rag | get_llm() | parser
rag_store = initialize_vector_store()

async def add_data(filename: str) -> bool:
    """
    Adds a text file to the vector database.
    """
    logger.info(f"Adding data to vector store{filename}")
    
    try:
        logger.info(f'Data for filename {filename}')
        if not filename.startswith(("Storage")):
            filename = f"Storage/{filename}"
        rag_store.add_data(filename)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to add data: {e}")
        return False

async def retrieve_context(question: str) -> str:
    """
    Retrieves relevant context from vector DB.
    """
    logger.info("Retrieving context for question", extra={"question": question})
    try:
        context = rag_store.query(question)
        return context
    except Exception as e:
        print(f"[ERROR] Retrieval failed: {e}")
        return ""

async def rag_answer(question: str , prompts:dict , memories:List) -> Response | dict:
    """
    Full RAG pipeline:
    1. Retrieve context
    2. Validate context
    3. Run LLM with strict grounding
    4. Parse structured output
    """
    logger.info("Starting RAG pipeline", extra={"question": question})
    print(prompts,memories,question)
    article =await retrieve_context(question)

    if not article:
        return {
            "Article": "",
            "Answer": "The requested information is not available in the provided documents."
        }
    logger.info(f"Prompt {prompts}")
    
    # Prompts = await get_all_start_methods(Session_ID)
    # memories = process_query(Session_ID, Session_ID, question)
    # answer = await rag_answer(question,Prompts,memories)
    # logger.info(f"Answer given by the rag {answer}")
    # await add_Prompt(answer.model_dump(),Session_ID)

    return rag_chain.invoke({
        "question": question,
        "Previous_Prompts":prompts,
        "Article": article,
        "format_instructions": parser.get_format_instructions(),
        "Memories":memories
    })

async def process_file_background(filename: str):
    """Background task to process and ingest file into vector DB.
    Args:
        filename (str): Name of the file to process
    returns:
        None"""
    logger.exception(f"Background file ingestion started {filename}", extra={"File to debug": filename})
        
    success = await add_data(filename)
    if not success:
        # Log instead of raising exception
        logger.error(f"Background ingestion failed for file: {filename}")
        

