from agent.state import AgentState
from agent.prompts import CLASSIFY_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from services.groq_client import llm
from pydantic import BaseModel

class ClassifyOutput(BaseModel):
    is_off_topic: bool
    is_specific: bool
    classify_reasoning: str

def classify_node(state: AgentState) -> AgentState:

    structured_llm = llm.with_structured_output(ClassifyOutput)

    response = structured_llm.invoke([
        SystemMessage(content=CLASSIFY_SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(content=state["user_query"]),
    ])

    
    return {
        **state,
        "is_off_topic": response.is_off_topic,
        "is_specific": response.is_specific,
        "classify_reasoning": response.classify_reasoning,
    }