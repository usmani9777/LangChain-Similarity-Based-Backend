from utils.mongo_memory import MongoMemoryStore
from utils.RuleBasedMemoryClassifier import RuleBasedMemoryClassifier
from models.LongMemory_Models import Memory
from core.config import settings
import logging
logger = logging.getLogger(__name__)

classifier = RuleBasedMemoryClassifier()
store = MongoMemoryStore(settings.mongo_url)

def process_query(user_id: str, session_id: str, query: str):
    memory_type = classifier.classify(query)
    logging.info(f"Memory Type Classified{memory_type}")
     
    if memory_type is None:
        logging.info(f"Memory Type is None Returning []")
        return []

    # Retrieve relevant memories
    memories = store.get_memories_by_type(
        session_id=session_id,
        memory_type=memory_type.value
    )
    logging.info(f"Retrieved Memory {memories}")
    memory_texts = [m["text"] for m in memories if "text" in m]
    

    # Create new memory
    memory = Memory(
        user_id=user_id,
        session_id=session_id,
        memory_type=memory_type,
        text=query
    )
    
    
    store.add_memory(memory.model_dump())
    logging.info(f"New Memory Created {memory}")

    return memory_texts
