import logging
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.output_parsers import PydanticOutputParser
# from langchain_classic.agents import AgentExecutor
# from langchain_core.agents import AgentExecutor
# from langchain_classic.agents import initialize_agent, AgentType

from models.Query_Payload import RagRequest, RedisQuery
from models.Response import Response
from core.prompt import SYSTEM_PROMPT_AGENTIC
from core.dependecies import get_llm
from Services.Rag import retrieve_context
# from Services.LongTermMemory import process_query
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
        for _ in range(5):
            print("Orchestration Loop Iteration")
            response = await self.llm_with_tools.ainvoke(self.messages)
            self.messages.append(response)

            if not response.tool_calls:
                # No more tools needed, move to synthesis
                break

            # 2. TOOL EXECUTION PHASE
            for call in response.tool_calls:
                if call["name"].lower() in ["json", "format"]: continue
                
                tool = next(t for t in ALL_TOOLS if t.name == call["name"])
                logger.info(f"Tools Called {call['name']}")
                # Manual ID Injection
                args = dict(call["args"])
                if "user_id" in args or "user_id" in tool.args_schema.model_fields:
                    args["user_id"] = self.payload.user_id
                if "session_id" in args or "session_id" in tool.args_schema.model_fields:
                    args["session_id"] = self.payload.Session_ID
                
                observation = tool.invoke(args)
                logger.info(f"Tool Output {call['name']}")
                self.messages.append(ToolMessage(tool_call_id=call["id"], content=str(observation)))

        # 3. SYNTHESIS PHASE (Fixes the "Raw Data" issue)
        # We use the raw 'llm' here so it focuses on human language, not tool selection
        # synthesis_prompt = self.messages + [
        #     HumanMessage(content=(
                
        #     "Tool calls are finished. Based on the data above, provide the final answer.There is no Tool Called JSON or json "
        #     "Synthesize everything into a human-friendly response. "
        #     "You have gathered the necessary information above. "
        #     "Now, synthesize the final answer. Convert raw lists or tool outputs into "
        #     "a natural, helpful response for the user. "
        #     "Output ONLY the following structure:\n{format_instructions}"
        #     ))
        # ]
        
        synthesis_prompt = self.messages + [
        HumanMessage(content=(
            "Tool calls are finished. "
            "You have retrieved the following user memories:\n"
            "There is no tool called JSON or json. "
            "Know answer the question based on the article, chat history, and memories provided.by the tools called. "
            f"Output ONLY the following structure: {parser.get_format_instructions()}"
        ))
]
        print("Synthesis Prompt Prepared")
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