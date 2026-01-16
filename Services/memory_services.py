from pyparsing import Optional
from logging import getLogger

from Services.Insession_Memory import DictSessionStore

logger = getLogger(__name__)
Memory_store = DictSessionStore()

Session_ID: str= None

async def SetSessionID():
    """Sets a unique session ID for the RAG store."""
    global Session_ID
    import uuid
    session_id = str(uuid.uuid4())
    
    logger.info(f"Session ID set to {session_id}")
    Session_ID = session_id
    return session_id

async def get_session_id():
    """Retrieves the current session ID."""
    global Session_ID
    if Session_ID is None:
        await SetSessionID()
    return Session_ID

async def add_Prompt(data):
    """Adds a prompt dictionary to the session store."""
    session_id = await get_session_id()
    Memory_store.add(session_id, data)
    logger.info("Prompt added to session store", extra={"session_id": session_id, "dict_id": data.get("id")})

async def get_all_start_methods():
    """Retrieves all stored dictionaries for the given session ID."""
    session_id = await get_session_id()
    dicts = Memory_store.get_latest(session_id)
    logger.info("Retrieved all start methods", extra={"session_id": session_id, "count": len(dicts)})
    return dicts



# store = DictSessionStore()

# # Add dictionaries
# store.add("session-1", {"id": "a1", "value": 100})
# store.add("session-1", {"id": "a2", "value": 200})
# store.add("session-1", {"id": "a3", "value": 300})

# # Retrieve by dict_id
# print(store.get("session-1", "a2"))
# # → [{'id': 'a2', 'value': 200}]

# # Empty dict_id
# print(store.get("session-1", None))
# # → []

# # Retrieve latest (max 5)
# print(store.get_latest("session-1"))
