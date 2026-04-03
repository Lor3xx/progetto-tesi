from agent.prompts import ENHANCE_RETRY_PROMPT, ENHANCE_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from services.groq_client import llm
from agent.state import AgentState
class EnhanceOutput(BaseModel):
    enhanced_query: str
    enhancement_reasoning: str
    missing_aspects: list[str]

def enhance_node(state: AgentState) -> AgentState:
    structured_llm = llm.with_structured_output(EnhanceOutput)

    if state["retry_count"] > 0:
        user_content = (
            f"Original query: {state['user_query']}\n"
            f"Previous enhanced query: {state['enhanced_query']}\n"
            f"Missing aspects: {', '.join(state['missing_aspects'])}"
        )
        messages = [
            SystemMessage(content=ENHANCE_RETRY_PROMPT),
            HumanMessage(content=user_content),
        ]
    else:
        messages = [
            SystemMessage(content=ENHANCE_SYSTEM_PROMPT),
            *state["messages"],
            HumanMessage(content=state["user_query"]),
        ]

    response = structured_llm.invoke(messages)

    return {
        **state,
        "enhanced_query": response.enhanced_query,
        "enhancement_reasoning": response.enhancement_reasoning,
        "missing_aspects": response.missing_aspects,
    }