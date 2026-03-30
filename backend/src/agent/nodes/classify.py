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
        category = parsed.get("category", "off_topic")
    except json.JSONDecodeError:
        category = "off_topic"

    return {
        **state,
        "is_generic_cybersecurity": category == "generic_cyber",
        "is_off_topic": category == "off_topic",
        "query_category": category,
    }