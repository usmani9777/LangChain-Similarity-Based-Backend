from pyparsing import Optional
from logging import getLogger
from fastapi import Request
from utils.Insession_Memory import RedisDictSessionStore
from models.Response import Response

logger = getLogger(__name__)


from core.config import settings


redis_url = settings.redis_url
ttl_seconds = settings.redis_ttl_seconds
key_prefix = settings.redis_key_prefix

Memory_store = RedisDictSessionStore(
        redis_url = redis_url,
        max_items  = 20,              # ✅ N = 20
        ttl_seconds  = ttl_seconds,           # ✅ TTL = 1 hour
        key_prefix = key_prefix)

Session_ID: str= None



async def add_Prompt(data:Response,SSID):
    """Adds a prompt dictionary to the session store."""
    Memory_store.add(SSID, data)
    logger.info("Prompt added to session store", extra={"session_id": SSID, "dict_id": data.get("id")})

async def get_all_start_methods(SSID):
    """Retrieves all stored dictionaries for the given session ID."""
    dicts = Memory_store.get_latest(SSID)
    logger.info("Retrieved all start methods", extra={"session_id": SSID, "count": len(dicts)})
    return dicts

async def Get_ALL():
    dicts = Memory_store.get_all_items()
    return dicts

async def Get_all_keys():
    dicts = Memory_store.get_all_keys()
    return dicts


def get_session_id(request: Request) -> str:
    return request.state.session_id



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
