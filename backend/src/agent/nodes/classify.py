from agent.state import AgentState
import json
from agent.prompts import CLASSIFY_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from services.groq_client import llm

def classify_node(state: AgentState) -> AgentState:
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
        # Se il parsing fallisce, assumiamo che la query sia specifica (default più sicuro)
        print("\n\nJSON parse error in classify, response was:", response.content, "\n\n\n")
        return {
            **state,
            "is_generic_cybersecurity": False,
            "is_off_topic": False,
            "classify_reasoning": "Parsing JSON fallito, classificazione di default a specifica."
        }
    
    return {
        **state,
        "is_off_topic": parsed.get("is_off_topic", False),
        "is_specific": parsed.get("is_specific", True),  # default a specifica se non chiaro
        "classify_reasoning": parsed.get("classify_reasoning", "No reasoning provided")
    }