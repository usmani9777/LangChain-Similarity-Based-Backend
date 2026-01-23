import logging
from typing import List, Union

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser

from models.Query_Payload import RagRequest, RedisQuery
from models.LongMemory_Models import Memory
from models.Response import Response
from core.prompt import SYSTEM_PROMPT
from core.dependecies import get_llm
from Services.Rag import retrieve_context
from Services.LongTermMemory import process_query
from Services.memory_services import get_all_start_methods
from utils.tools import ALL_TOOLS

logger = logging.getLogger(__name__)

# -------------------------------
# Output parser
# -------------------------------
parser = PydanticOutputParser(pydantic_object=Response)

def is_question(text: str) -> bool:
    text = text.strip().lower()
    return (
        text.endswith("?")
        or text.startswith(("what", "why", "how", "when", "where", "who"))
    )
def get_qa_pairs(responses: List[dict]) -> List[str]:
    """
    Transforms a list of dictionaries into a list of formatted strings.
    Handles 'dict' objects correctly.
    """
    # Use .get() to avoid KeyErrors if the dictionary is malformed
    return [
        f"Question: {r.get('Question', 'N/A')} | Answer: {r.get('Answer', 'N/A')}" 
        for r in responses
    ]
# -------------------------------
# Main RAG function
# -------------------------------
async def rag_answer_tool_enabled(
    payload: RagRequest
):

    logger.info("Starting RAG pipeline", extra={"question": payload.question})

    # 1️⃣ Retrieve article context
    article = await retrieve_context(payload.question)
    

    # 2️⃣ Detect memory intent
    redis_query = RedisQuery(
        user_id=payload.user_id,
        session_id=payload.Session_ID,
        query=payload.question
    )
    memory_type, _ = await process_query(redis_query)

    # 3️⃣ Retrieve memories (MANUAL TOOL CALL)
    memories: List[str] = []
    if memory_type:
        retrieve_tool = ALL_TOOLS[0]
        memories = retrieve_tool.invoke({
            "user_id": payload.user_id,
            "memory_type": memory_type.value
        })

    # 4️⃣ Previous chat history
    previous_prompts = await get_all_start_methods(payload.Session_ID)
    previous_prompts = get_qa_pairs(previous_prompts)

    # 5️⃣ Create LLM with tools
    llm = get_llm()
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    # 6️⃣ First LLM call
    messages = [
        SystemMessage(
        content=SYSTEM_PROMPT.format(
          
            Memories=memories,
            Previous_Prompts=previous_prompts,
            format_instructions=parser.get_format_instructions()
        )
    ),
        HumanMessage(
            content=f"""
Question: {payload.question}

Article:
{article}

Previous Prompts:
{previous_prompts}

User Memories:
{memories}
Format Instruction:
{parser.get_format_instructions()}
"""
        )
    ]

    ai_message = llm_with_tools.invoke(messages)

    # 7️⃣ Tool execution loop
    tool_messages = []

    if ai_message.tool_calls:
        for call in ai_message.tool_calls:
            if call["name"] == "json":
                continue
            tool = next(t for t in ALL_TOOLS if t.name == call["name"])
            # 2. Extract arguments
            tool_args = call["args"]
            
            # 3. Inject IDs if it's the save_memory tool
            if call["name"] == "save_memory":
                tool_args["user_id"] = payload.user_id
                tool_args["session_id"] = payload.Session_ID
            
            if call["name"] == "retrieve_memories":
                tool_args["user_id"] = payload.user_id
                
                
            

            # ✅ IMPORTANT: tool.invoke expects ONE dict
            tool_result = tool.invoke(call["args"])

            tool_messages.append(
                ToolMessage(
                    tool_call_id=call["id"],
                    content=str(tool_result)
                )
            )

        # 8️⃣ Second LLM call with tool outputs
        reminder_message = HumanMessage(content=(
                "All the tool Calling is Done here the Article know answer {article} know answer"
                "I have provided the raw memory data above. "
                "Now, synthesize this information into a natural, human-friendly answer. "
                "Do NOT list the raw data. Do NOT mention the tools. "
                f"if Article present Use it to Answer this is the Question: {payload.question}"
                f"Output ONLY the {parser.get_format_instructions()}."
            ))

        final_message = llm_with_tools.invoke(
            [ai_message] + tool_messages + [reminder_message]
        )

    else:
        final_message = ai_message

    # 9️⃣ Parse final output
    final_answer: Response = parser.invoke(final_message)

    return final_answer
