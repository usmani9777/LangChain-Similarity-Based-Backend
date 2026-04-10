from fastapi import Request
from models.LongMemory_Models import Create_Memory, Memory
from core.dependecies import Get_Classifier, Monogo_Memory
import logging
from models.Query_Payload import RedisQuery
from langchain.tools import tool
from typing import List


logger = logging.getLogger(__name__)


@tool
def retrieve_memories(user_id: str, memory_type: str) -> List[str]:
    """
    Retrieve stored memories of a specific type for a given user.

    This tool fetches memories from the MongoDB memory store filtered by 
    memory type (e.g., "Goal", "Personal", "Fact") for the specified user ID.
    Only the text of each memory is returned.

    Args:
        user_id (str): Unique identifier of the user.
        memory_type (str): Type of memory to retrieve ("Goal", "Personal", "Fact").

    Returns:
        List[str]: A list of memory texts corresponding to the given type.
    
    Example:
        >>> memories = await retrieve_memories("user123", "Goal")
        >>> print(memories)
        ["I want to learn Python", "I aim to build a smart traffic system"]
    """
    try:
        # Initialize memory store
        store = Monogo_Memory()
        
        # Fetch memories of the given type
        memories = store.get_memories_by_type(
            user_id=user_id,
            memory_type=memory_type
        )
        print('Memorys Retrieved:', memories)
        logging.info(f"[MemoryTool] Retrieved {len(memories)} memories for user '{user_id}' of type '{memory_type}'")
        
        # Extract text from memories
        memory_texts = [m.get("text", "") for m in memories if "text" in m]

        return memory_texts

    except Exception as e:
        logging.error(f"[MemoryTool] Failed to retrieve memories: {e}")
        return []



@tool
def save_memory(user_id: str, session_id: str, memory_type: str, text: str) -> str:
    """
    Save a memory object to the long-term memory store.

    This tool takes a Memory object (Pydantic model), serializes it,
    and stores it in the MongoDB memory collection.

    Args:
        Payload (Memory): The memory object to store.

    Returns:
        str: Success message after storing the memory.

    Example:
        >>> input = (memory_type="Goal",  text="Learn Python")
        >>> await save_memory(memory_obj)
        "Memory saved successfully."
    """
    try:
       
        store = Monogo_Memory()
        memory = Memory(
            user_id=user_id,
            session_id= session_id,
            memory_type=memory_type,
            text=text
         )
        store.add_memory(memory.model_dump())
        logging.info(f"[MemoryTool] New memory created: {memory}")
        return "Memory saved successfully."
    except Exception as e:
        logging.error(f"[MemoryTool] Failed to save memory: {e}")
        return f"Failed to save memory: {e}"

def get_session_id(request: Request) -> str:
            return request.state.session_id