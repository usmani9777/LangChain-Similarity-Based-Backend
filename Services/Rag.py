# from langchain_openai import ChatOpenAI
# import os 
# from langchain_openai import ChatOpenAI
# from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
# from langchain_core.output_parsers import PydanticOutputParser
# from typer import prompt
# from models.Response import Rag
# from Services.db import TextRAGVectorStore

# from dotenv import load_dotenv
# load_dotenv()
# Api_Key = os.getenv('API_KEY')
# Base_URL = os.getenv('BASE_URL')
# Model_name = os.getenv('MODEL_NAME')


# LLM = ChatOpenAI(model_name=Model_name, base_url=Base_URL, api_key=Api_Key, temperature=0)
# parser = PydanticOutputParser(pydantic_object=Rag)
# prompt_rag = ChatPromptTemplate.from_messages([
#     (
#         "system", 
#         "You are an expert RAG assistant. Your task is to answer the user's query strictly using the provided Article.\n\n"
#         "### CONTEXT GUIDELINES:\n"
#         "1. Use ONLY the provided Article to answer the question.\n"
#         "2. If the answer is not contained within the Article, explicitly state that the information is not available.\n"
#         "3. Do not use outside knowledge or hallucinate facts.\n\n"
#         "### FORMATTING:\n"
#         "{format_instructions}"
#     ),
#     (
#         "user", 
#         "--- ARTICLE START ---\n"
#         "{Article}\n"
#         "--- ARTICLE END ---\n\n"
#         "QUERY: {question}"
#     )
# ])
# response = prompt_rag | LLM | parser

# try:
#     rag = TextRAGVectorStore(
#          paths=["Storage/file.txt"],
#          rebuild=True
#      )
# except Exception as e:
#     print(f"Error initializing RAG Vector Store: {e}")
# finally:
#     rag = TextRAGVectorStore(
#          rebuild=False
#      )

# def add_data(filename):
#     rag.add_data(f"Storage/{filename}")
#     return True
    
# def retrival(question):
#     return rag.query(question)

# def Rag_func(Question):  
#     Article = retrival(Question)
#     return response.invoke({"question": Question, "format_instructions": parser.get_format_instructions(), "Article": Article})



from typing import List, Optional
from models.Response import Response
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.prompt import prompt_rag
from utils.db import TextRAGVectorStore

from logging import getLogger

logger = getLogger(__name__)

from core.config import settings

API_KEY = settings.api_key
BASE_URL = settings.base_url
MODEL_NAME = settings.model_name

llm = ChatOpenAI(
    model_name=MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0
)

parser = PydanticOutputParser(pydantic_object=Response)



# prompt_rag = ChatPromptTemplate.from_messages([
#     (
#         "system",
#         "You are an expert RAG assistant. You must answer questions using a combination of "
#         "the provided Article, User Memories, and Previous Chat History.\n\n"
        
#         "### KNOWLEDGE SOURCE PRIORITY:\n"
#         "1. **Context Synthesis:** Treat the 'Article', 'User Memories', and 'User History' "
#         "as a single integrated knowledge base. If the answer is in any of these, provide it.\n"
#         "2. **Specific Recall:** If the user asks about personal details, goals, or facts "
#         "shared previously, prioritize the 'User Memories' section.\n"
#         "3. **Tone & Context:** Use 'User History' to ensure continuity in the conversation.\n"
#         "4. **Strictness:** Only say 'The requested information is not available...' if the "
#         "answer is missing from ALL provided sections (Article, Memories, and History).\n\n"
        
#         "### RULES:\n"
#         "- Do not make up facts. Use only the provided data.\n"
#         "- If information in the Article conflicts with User Memories, prioritize the User Memories "
#         "as the user's personal truth.\n\n"
        
#         "### DATA SECTIONS:\n"
#         "User Memories: {Memories}\n"
#         "User History: {Previous_Prompts}\n\n"
        
#         "### FORMATTING:\n"
#         "{format_instructions}"
#     ),
#     (
#         "user",
#         "--- ARTICLE START ---\n"
#         "{Article}\n"
#         "--- ARTICLE END ---\n\n"
#         "QUESTION: {question}"
#     )
# ])
# RAG Chain
rag_chain = prompt_rag | llm | parser

def initialize_vector_store() -> TextRAGVectorStore:
    """
    Initializes the vector store.
    Rebuilds if initial data exists, otherwise loads existing DB.
    """
    try:
        logger.info("[INFO] Initializing vector store")
        return TextRAGVectorStore(paths=["Storage/file.txt"], rebuild=True)
    
    except Exception as e:
        print(f"[WARN] Vector store rebuild failed: {e}")
        return TextRAGVectorStore(rebuild=False)


    
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
        

