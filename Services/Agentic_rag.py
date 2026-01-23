import logging
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_classic.agents import AgentExecutor
# from langchain_core.agents import AgentExecutor
from langchain_classic.agents import initialize_agent, AgentType

from models.Query_Payload import RagRequest, RedisQuery
from models.Response import Response
from core.prompt import SYSTEM_PROMPT_AGENTIC
from core.dependecies import get_llm
from Services.Rag import retrieve_context
from Services.LongTermMemory import process_query
from Services.memory_services import get_all_start_methods
from utils.tools import ALL_TOOLS

logger = logging.getLogger(__name__)

# # -------------------------------
# # Output parser
# # -------------------------------
parser = PydanticOutputParser(pydantic_object=Response)

def get_qa_pairs(responses: List[dict]) -> List[str]:
    return [
        f"Question: {r.get('Question', 'N/A')} | Answer: {r.get('Answer', 'N/A')}" 
        for r in responses
    ]

# # -------------------------------
# # Agentic RAG function
# # -------------------------------
# async def rag_agentic(payload: RagRequest) -> Response:
#     logger.info("Starting Agentic RAG pipeline", extra={"question": payload.question})

#     # 1️⃣ Retrieve article context
#     article = await retrieve_context(payload.question)

#     # 2️⃣ Detect memory intent
#     redis_query = RedisQuery(
#         user_id=payload.user_id,
#         session_id=payload.Session_ID,
#         query=payload.question
#     )
#     memory_type, _ = await process_query(redis_query)

#     # 3️⃣ Retrieve previous chat history
#     previous_prompts = await get_all_start_methods(payload.Session_ID)
#     previous_prompts = get_qa_pairs(previous_prompts)

#     # 4️⃣ Create LLM
#     llm = get_llm()
#     agent = initialize_agent(
#         tools=ALL_TOOLS,
#         llm=llm,
#         agent=AgentType.OPENAI_FUNCTIONS,
#         verbose=True
#         )
    
#     system_prompt_filled = SYSTEM_PROMPT_AGENTIC.format(
#     Memories=[],  # initially empty; agent can retrieve
#     Previous_Prompts=previous_prompts,
#     Article=article,
#     format_instructions=parser.get_format_instructions()
#     )

#     # 5️⃣ Initialize agent executor with all tools
#     # agent = AgentExecutor(
#     #     llm=llm,
#     #     tools=ALL_TOOLS,
#     #     system_message=SystemMessage(
#     #         content=SYSTEM_PROMPT_AGENTIC.format(
#     #             Memories=[],  # initially empty, agent can retrieve
#     #             Previous_Prompts=previous_prompts,
#     #             format_instructions=parser.get_format_instructions(),
#     #             Article =article
#     #         )
#     #     ),
#     #     output_parser=parser
#     # )

#     # # 6️⃣ Run agent with full user query and article
#     final_answer: Response = await agent.arun(
#         input=(
#             f"{system_prompt_filled}\n\n"
#             f"Question: {payload.question}\n\n"
#             f"Article:\n{article}\n\n"
#             f"Previous Prompts:\n{previous_prompts}\n\n"
#             "Use available tools to retrieve memories or save them if needed. "
#             "Do NOT output raw tool calls; produce a human-friendly answer. "
#             f"Output ONLY the {parser.get_format_instructions()}."
#         ),
#         metadata={"user_id": payload.user_id, "session_id": payload.Session_ID, "memory_type": memory_type.value if memory_type else None}
#     )

#     # return final_answer
#     # final_answer_str = await agent.run(
#     # {"input": system_prompt_filled, "metadata": {
#     #     "user_id": payload.user_id,
#     #     "session_id": payload.Session_ID,
#     #     "memory_type": memory_type.value if memory_type else None
#     # }}
#     #     )

#     # final_answer: Response = parser.parse(final_answer_str)
#     return final_answer

    
class RagOrchestrator:
    def __init__(self, payload: RagRequest, article: str, history: List[str]):
        self.payload = payload
        self.article = article
        self.history = history
        self.llm = get_llm()
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self.messages = [
            SystemMessage(content=SYSTEM_PROMPT_AGENTIC.format(
                Memories=[], 
                Previous_Prompts=self.history,
                format_instructions=parser.get_format_instructions(),
                Article = self.article
            )),
            HumanMessage(content=f"Article: {self.article}\n\nQuestion: {self.payload.question}")
        ]

    async def run(self) -> Response:
        # 1. ORCHESTRATION LOOP (Max 3 iterations to prevent infinite loops)
        for _ in range(3):
            response = await self.llm_with_tools.ainvoke(self.messages)
            self.messages.append(response)

            if not response.tool_calls:
                # No more tools needed, move to synthesis
                break

            # 2. TOOL EXECUTION PHASE
            for call in response.tool_calls:
                if call["name"].lower() in ["json", "format"]: continue
                
                tool = next(t for t in ALL_TOOLS if t.name == call["name"])
                
                # Manual ID Injection
                args = dict(call["args"])
                if "user_id" in args or "user_id" in tool.args_schema.model_fields:
                    args["user_id"] = self.payload.user_id
                if "session_id" in args or "session_id" in tool.args_schema.model_fields:
                    args["session_id"] = self.payload.Session_ID
                
                observation = tool.invoke(args)
                self.messages.append(ToolMessage(tool_call_id=call["id"], content=str(observation)))

        # 3. SYNTHESIS PHASE (Fixes the "Raw Data" issue)
        # We use the raw 'llm' here so it focuses on human language, not tool selection
        synthesis_prompt = self.messages + [
            HumanMessage(content=(
                
            "Tool calls are finished. Based on the data above, provide the final answer.There is no Tool Called JSON or json "
            "Synthesize everything into a human-friendly response. "
                "You have gathered the necessary information above. "
                "Now, synthesize the final answer. Convert raw lists or tool outputs into "
                "a natural, helpful response for the user. "
                f"Output ONLY the following structure: {parser.get_format_instructions()}"
            ))
        ]
        
        final_response = await self.llm.ainvoke(synthesis_prompt)
        return self._parse_result(final_response.content)

    def _parse_result(self, content: str) -> Response:
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            return parser.parse(content[start:end])
        except Exception:
            return Response(Status_Code=500, Answer=content, Question=self.payload.question)

# 4. Entry Point Function
async def rag_agentic_orchestrated(payload: RagRequest):
    article = await retrieve_context(payload.question)
    history_raw = await get_all_start_methods(payload.Session_ID)
    history = get_qa_pairs(history_raw)

    orchestrator = RagOrchestrator(payload, article, history)
    return await orchestrator.run()