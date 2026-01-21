from models.LongMemory_Models import Create_Memory, Memory
from core.dependecies import Get_Classifier, Monogo_Memory
import logging
from models.Query_Payload import RedisQuery

logger = logging.getLogger(__name__)

async def process_query(payload : RedisQuery):
    classifier = Get_Classifier()
    memory_type = classifier.classify(payload.query)
    logging.info(f"Memory Type Classified{memory_type}")
     
    if memory_type is None:
        logging.info(f"Memory Type is None Returning []")
        return None,[]

    # Retrieve relevant memories
    store = Monogo_Memory()
    memories = store.get_memories_by_type(
        session_id=payload.session_id,
        memory_type=memory_type.value
    )
    logging.info(f"Retrieved Memory {memories}")
    memory_texts = [m["text"] for m in memories if "text" in m]
    

    # Create new memory
    # memory = Memory(
    #     user_id=payload.user_id,
    #     session_id=payload.session_id,
    #     memory_type=memory_type,
    #     text=payload.query
    # )
    
    # store.add_memory(memory.model_dump())
    # logging.info(f"New Memory Created {memory}")

    return memory_type,memory_texts

async def Create_memory(Payload:Memory):
    store = Monogo_Memory()
     # Create new memory    
    store.add_memory(Payload.model_dump())
    logging.info(f"New Memory Created {Payload}")
    