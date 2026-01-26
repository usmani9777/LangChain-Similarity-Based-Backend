# # import logging
# # from typing import List

# # from langchain_classic.agents import AgentExecutor, create_openai_functions_agent
# # from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# # from langchain_core.output_parsers import PydanticOutputParser
# # from langchain_core.runnables import RunnableLambda

# # from models.Query_Payload import RagRequest
# # from models.Response import Response
# # from core.prompt import SYSTEM_PROMPT_AGENTIC
# # from core.dependecies import get_llm
# # from Services.Rag import retrieve_context
# # from Services.memory_services import get_all_start_methods
# # from utils.tools import ALL_TOOLS

# # logger = logging.getLogger(__name__)

# # # -------------------------------
# # # Output Parser
# # # -------------------------------
# # parser = PydanticOutputParser(pydantic_object=Response)


# # def get_qa_pairs(responses: List[dict]) -> List[str]:
# #     return [
# #         f"Question: {r.get('Question', 'N/A')} | Answer: {r.get('Answer', 'N/A')}"
# #         for r in responses
# #     ]


# # # -------------------------------
# # # Prompt Template (STRICT)
# # # -------------------------------
# # # PROMPT = ChatPromptTemplate.from_messages([
# # #     ("system", SYSTEM_PROMPT_AGENTIC),
# # #     MessagesPlaceholder(variable_name="chat_history"),
# # #     MessagesPlaceholder(variable_name="agent_scratchpad"),
# # #     ("human",
# # #      "Article:\n{Article}\n\n"
# # #      "User Question:\n{question}\n\n"
     
# # #      "All tool calls are complete. Answer the USER QUESTION above.\n\n"
# # #      "{format_instructions}\n\n"
# # #      "Rules:\n"
# # #      "- Question field must equal the user's question exactly\n"
# # #      "- Saving must be exactly one of: Personal, Goal, Fact, None\n"
# # #      "- Article must be a string\n"
# # #      "- Return ONLY valid JSON\n"
# # #     )
# # # ])

# # PROMPT = ChatPromptTemplate.from_messages([
# #     ("system", SYSTEM_PROMPT_AGENTIC),
# #     MessagesPlaceholder(variable_name="chat_history"),
# #     MessagesPlaceholder(variable_name="agent_scratchpad"),
# #     ("human",
# #      "Article:\n{Article}\n\n"
# #      "User Question:\n{question}\n\n"
# #      "If memory retrieval or saving is needed, CALL THE TOOLS.\n"
# #      "After tools finish, return the final answer.\n\n"
# #      "{format_instructions}\n\n"
# #      "Rules:\n"
# #      "- Question field must equal the user's question exactly\n"
# #      "- Saving must be exactly one of: Personal, Goal, Fact, None\n"
# #      "- Article must be a string\n"
# #      "- Return ONLY valid JSON\n"
# #     )
# # ])

# # # -------------------------------
# # # Agent Factory
# # # -------------------------------
# # def build_agent_executor():
# #     llm = get_llm()
# #     llm.callbacks = None

# #     agent = create_openai_functions_agent(
# #         llm=llm,
# #         tools=ALL_TOOLS,
# #         prompt=PROMPT
# #     )

# #     base_executor = AgentExecutor(
# #         agent=agent,
# #         tools=ALL_TOOLS,
# #         verbose=True,
# #         max_iterations=3,
# #         handle_parsing_errors=True,
# #         return_intermediate_steps=True
# #     )

# #     # 🔥 Enforce structured output
# #     return base_executor | RunnableLambda(lambda r: parser.parse(r["output"]))


# # agent_executor = build_agent_executor()


# # # -------------------------------
# # # Public Entry Function
# # # -------------------------------
# # async def rag_agentic_executor(payload: RagRequest) -> Response:
# #     """
# #     Agentic RAG using AgentExecutor (tool calling + memory + RAG)
# #     """
# #     try:
# #         # 1. Retrieve RAG context
# #         article_docs = await retrieve_context(payload.question)
# #         article_text = "\n\n".join(d.page_content for d in article_docs)

# #         # 2. Retrieve memory history
# #         history_raw = await get_all_start_methods(payload.Session_ID)
# #         chat_history = get_qa_pairs(history_raw)

# #         # 3. Prepare agent input
# #         agent_input = {
# #             "question": payload.question,
# #             "Article": article_text,
# #             "chat_history": [''],
# #             "Memories": [],
# #             "Previous_Prompts": chat_history,
# #             "format_instructions": parser.get_format_instructions(),
# #         }

# #         # 4. Execute agent
# #         return agent_executor.invoke(agent_input,
# #                                       config={
# #         "configurable": {
# #             "user_id": payload.user_id,
# #             "session_id": payload.Session_ID
# #         }
# #     })

# #     except Exception as e:
# #         logger.exception("Agentic RAG failed")
# #         return Response(
# #             Status_Code=500,
# #             Answer=str(e),
# #             Question=payload.question,
# #             Saving="None",
# #             Article=""
# #         )

import logging
import json
from typing import List

from langchain_classic.agents import AgentExecutor, create_openai_functions_agent, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from models.Query_Payload import RagRequest
from models.Response import Response
from core.dependecies import get_llm
from Services.Rag import retrieve_context
from Services.memory_services import get_all_start_methods
from utils.tools import ALL_TOOLS_AGENT

logger = logging.getLogger(__name__)



SYSTEM_PROMPT_AGENTIC = """
==================================================
ROLE
==================================================
You are an expert RAG assistant and autonomous agent.

You have access to three tools only:
- retrieve_memories_config
- save_memory_config
- add

Your responsibilities:
1. Synthesize raw data into natural, human-friendly responses.
2. Gracefully acknowledge personal facts from memory when relevant.

==================================================
AGENTIC AI RULES
==================================================
• You decide when to call tools.
• Use retrieve_memories_config when personal context is required.
• Use save_memory_config automatically when the user provides clear personal facts.
• Never mention tools or tool calls in your final response.

==================================================
MANDATORY MEMORY SAVE TRIGGER (CRITICAL)
==================================================
Call save_memory_config if user input contains:
• "I am <name>"
• "My name is <name>"
• "I work at <company>"
• "I live in <city>"
• "My goal is <goal>"
• "I prefer <style>"

This must happen before responding.

==================================================
WHEN NOT TO SAVE
==================================================
Do NOT save memory if input is:
• A question
• A calculation
• A request
• General knowledge
• A repeat of stored memory

==================================================
RETRIEVE MEMORIES (MANDATORY WHEN NEEDED)
==================================================
Call retrieve_memories_config if:
1. The user asks about themselves
2. Personal context is empty
3. The article does not contain the answer

Never answer “not available” without retrieving memories.

==================================================
KNOWLEDGE PRIORITY
==================================================
1. Retrieved user memories
2. Article context
3. Chat history

==================================================
MEMORY SYNTHESIS RULE
==================================================
When using memories:
• Do NOT list memories verbatim
• Do NOT concatenate entries
• Deduplicate
• Resolve conflicts
• Summarize naturally

==================================================
ANSWER SYNTHESIS RULES
==================================================
• Never expose raw memory text
• Never repeat database entries
• Always infer and summarize naturally
• Acknowledge personal facts briefly when relevant

==================================================
FINAL RESPONSE RULE (ABSOLUTE)
==================================================
If a tool is required:
→ Call the tool silently first
→ Then output ONLY the final human response

Never output JSON.
Never describe tool usage.
Never show intermediate steps.

==================================================
DATA CONTEXT (PREVIEW)
==================================================
User Memories: {Memories}
Chat History: {Previous_Prompts}
Article Context: {Article}

==================================================
AGENTIC REASONING FLOW
==================================================
1. Check if memory save is required
2. Check if memory retrieval is required
3. Use article/chat if needed
4. Respond naturally to the user
"""

# -------------------------------
# Output Parser
# -------------------------------
parser = PydanticOutputParser(pydantic_object=Response)


# -------------------------------
# Helpers
# -------------------------------
def get_qa_pairs(responses: List[dict]) -> List[str]:
    return [
        f"Question: {r.get('Question', 'N/A')} | Answer: {r.get('Answer', 'N/A')}"
        for r in responses
    ]


# -------------------------------
# Prompt Template (STRICT JSON)
# # -------------------------------
# PROMPT = ChatPromptTemplate.from_messages([
#     ("system", SYSTEM_PROMPT_AGENTIC),
#     MessagesPlaceholder(variable_name="chat_history"),
#     MessagesPlaceholder(variable_name="agent_scratchpad"),
#      ("human",
#      "Article:\n{Article}\n\n"
#      "User Question:\n{question}\n\n"
#      "If memory retrieval or saving is required, CALL THE TOOL.\n"
#      "After tools complete, return the final answer.\n\n"
#      "{format_instructions}\n\n"
#      "Rules:\n"
#      "- Question must equal the user's question exactly\n"
#      "- Saving must be one of: Personal, Goal, Fact, None\n"
#      "- Article must be a string\n"
#      "- Return ONLY valid JSON\n"
#     )
# ])



# PROMPT = ChatPromptTemplate.from_messages([
#     ("system", SYSTEM_PROMPT_AGENTIC),
#     # 1. Past conversation context
#     MessagesPlaceholder(variable_name="chat_history"), 
#     # 2. The current task
#     ("human", "Article context:\n{Article}\n\nQuestion: {question}"), 
#     # 3. The "Work Area" where tool results live
#     MessagesPlaceholder(variable_name="agent_scratchpad"), 
#     # 4. Final instruction (only seen when tools are done)
#     ("human", "Now, provide the final response in this format: {format_instructions}")
# ])
PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT_AGENTIC),
    MessagesPlaceholder(variable_name="chat_history"), 
    ("human", "CONTEXT:\nArticle: {Article}\nUser Question: {question}"), 
    MessagesPlaceholder(variable_name="agent_scratchpad"), 
    ("human", (
        "STRICT RULE: You must respond ONLY with a JSON object. "
        "Do not include any conversational text outside the JSON. "
        "Follow this format exactly: {format_instructions}"
    ))  
])
# -------------------------------
# Agent Factory (SAFE)
# -------------------------------
def build_agent_executor():
    llm = get_llm()
    
    agent = create_tool_calling_agent(
        llm=llm,
        tools=ALL_TOOLS_AGENT,
        prompt=PROMPT
    )

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS_AGENT,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True,
        # return_intermediate_steps=True is fine here
    )
    
agent_executor = build_agent_executor()


# -------------------------------
# Robust JSON Extractor
# -------------------------------
def extract_json(text: str) -> dict:
    """
    Extract first valid JSON object from model output safely.
    """
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("No JSON found in model output")
        return json.loads(text[start:end])


# -------------------------------
# Output Parsing
# -------------------------------
def parse_agent_output(result: dict, question: str) -> Response:
    try:
        raw = result.get("output", "")
        data = extract_json(raw)
        return Response(**data)
    except Exception as e:
        logger.exception("Output parsing failed")
        return Response(
            Status_Code=500,
            Answer=result.get("output", ""),
            Question=question,
            Saving="None",
            Article=""
        )


# -------------------------------
# Public Entry Function
# -------------------------------
async def rag_agentic_executor(payload: RagRequest) -> Response:
    """
    Agentic RAG using AgentExecutor (tool calling + memory + RAG)
    """
    try:
        # 1. Retrieve RAG context
        article_docs = await retrieve_context(payload.question)
        article_text = "\n\n".join(d.page_content for d in article_docs)

        # 2. Retrieve memory history
        history_raw = await get_all_start_methods(payload.Session_ID)
        chat_history = get_qa_pairs(history_raw)

        # 3. Prepare agent input
        agent_input = {
            "question": payload.question,
            "Article": article_text,
            "chat_history": [''],
            'Memories' : [],
            "format_instructions": parser.get_format_instructions(),
            "Previous_Prompts": ['']
        }

        # 4. Execute agent
        result = agent_executor.invoke(
            agent_input,
            config={
                "configurable": {
                    "user_id": payload.user_id,
                    "session_id": payload.Session_ID
                },
                "tags": ["agent-request"],
                "metadata": {"source": "rag_executor"}
            }
        )
        # 5. Parse safely
        return parse_agent_output(result, payload.question)

    except Exception as e:
        logger.exception("Agentic RAG failed")
        return Response(
            Status_Code=500,
            Answer=str(e),
            Question=payload.question,
            Saving="None",
            Article=""
        )

