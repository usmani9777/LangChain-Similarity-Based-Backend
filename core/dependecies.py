from functools import lru_cache
from langchain_openai import ChatOpenAI
from core.config import settings
from utils.db import TextRAGVectorStore
from logging import getLogger
from utils.Insession_Memory import RedisDictSessionStore
from utils.RuleBasedMemoryClassifier import RuleBasedMemoryClassifier
from utils.mongo_memory import MongoMemoryStore
logger = getLogger(__name__)

@lru_cache
def get_llm():
    return ChatOpenAI(
        model_name=settings.model_name,
        base_url=settings.base_url,
        api_key=settings.api_key,
        temperature=0,
        timeout=30,
        max_retries=2,
        streaming=False,
        callbacks=None # Make sure no callback is passed
    )
    
@lru_cache
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
    
@lru_cache
def Get_redis() -> RedisDictSessionStore:
    return RedisDictSessionStore()
    
@lru_cache
def Get_Classifier() -> RuleBasedMemoryClassifier:
    return RuleBasedMemoryClassifier()

@lru_cache
def Monogo_Memory() -> MongoMemoryStore:
    return MongoMemoryStore(settings.mongo_url)
    
    
# from functools import lru_cache
# from langchain_openai import ChatOpenAI
# from core.config import settings
# from utils.db import TextRAGVectorStore
# from logging import getLogger

# logger = getLogger(__name__)

# @lru_cache
# def get_llm() -> ChatOpenAI:
#     logger.info("Initializing LLM client")
#     return ChatOpenAI(
#         model_name=settings.model_name,
#         base_url=settings.base_url,
#         api_key=settings.api_key,
#         temperature=0,
#         timeout=30,
#         max_retries=2,
#     )

# @lru_cache
# def get_vector_store() -> TextRAGVectorStore:
#     """
#     Loads existing vector DB.
#     NEVER rebuilds at runtime.
#     """
#     logger.info("Loading vector store (read-only)")
#     return TextRAGVectorStore(
#         persist_dir=settings.storage_dir,
#         rebuild=False
#     )
