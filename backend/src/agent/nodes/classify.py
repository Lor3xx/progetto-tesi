from agent.state import AgentState
import json
from agent.prompts import CLASSIFY_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState
from services.groq_client import llm_eval

def classify_node(state: AgentState) -> AgentState:
    response = llm_eval.invoke([
        SystemMessage(content=CLASSIFY_SYSTEM_PROMPT),
        HumanMessage(content=state["user_query"]),
    ])

    try:
        clean = (response.content.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        # Se il parsing fallisce, assumiamo che la query sia specifica (default più sicuro)
        return {
            **state,
            "is_generic_cybersecurity": False,
            "is_off_topic": False,
        }
    
    return {
        **state,
        "is_off_topic": parsed.get("is_off_topic", False),
    }