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


import os
from dotenv import load_dotenv
from typing import Optional
from models.Response import Response
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from Services.db import TextRAGVectorStore

from logging import getLogger

logger = getLogger(__name__)


load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    model_name=MODEL_NAME,
    base_url=BASE_URL,
    api_key=API_KEY,
    temperature=0
)

parser = PydanticOutputParser(pydantic_object=Response)

prompt_rag = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert Retrieval-Augmented Generation (RAG) assistant.\n\n"
        "RULES:\n"
        "1. Answer the user's question using ONLY the provided Article.\n"
        "2. If the answer is not explicitly found in the Article, respond with:\n"
        "'The requested information is not available in the provided documents.'\n"
        "3. Do NOT use outside knowledge or assumptions.\n\n"
        "These Are User Previouse Prompts also take them into account {Previous_Prompts} also take them in account when answering"
        "FORMAT:\n"
        "{format_instructions}"
        
    ),
    (
        "user",
        "--- ARTICLE START ---\n"
        "{Article}\n"
        "--- ARTICLE END ---\n\n"
        "QUESTION: {question}"
    )
])

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

async def rag_answer(question: str , prompts:dict) -> Response | dict:
    """
    Full RAG pipeline:
    1. Retrieve context
    2. Validate context
    3. Run LLM with strict grounding
    4. Parse structured output
    """
    logger.info("Starting RAG pipeline", extra={"question": question})

    article =await retrieve_context(question)

    if not article:
        return {
            "Article": "",
            "Answer": "The requested information is not available in the provided documents."
        }

    return rag_chain.invoke({
        "question": question,
        "Previous_Prompts":prompts,
        "Article": article,
        "format_instructions": parser.get_format_instructions()
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
        

