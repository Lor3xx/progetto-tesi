from agent.state import AgentState
from agent.prompts import CLASSIFY_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from services.groq_client import llm
from pydantic import BaseModel
import json

class ClassifyOutput(BaseModel):
    is_off_topic: bool
    is_specific: bool
    classify_reasoning: str

def classify_node(state: AgentState) -> AgentState:

    structured_llm = llm.with_structured_output(ClassifyOutput)

    response = llm.invoke([
        SystemMessage(content=CLASSIFY_SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(content=state["user_query"]),
    ])

    try:
        clean = (response.content.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = {"is_off_topic": False, "is_specific": False, "classify_reasoning": "parse error"}

    
    return {
        **state,
        "is_off_topic": parsed["is_off_topic"],
        "is_specific": parsed["is_specific"],
        "classify_reasoning": parsed["classify_reasoning"],
    }