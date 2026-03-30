from agent.prompts import ENHANCE_RETRY_PROMPT, ENHANCE_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from config import settings
from services.groq_client import llm
from agent.state import AgentState

def enhance_node(state: AgentState) -> AgentState:
    import json

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
            HumanMessage(content=state["user_query"]),
        ]

    response = llm.invoke(messages)

    try:
        clean = (response.content.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        # fallback se il modello non rispetta il JSON
        print("\n\nJSON parse error in enhance_node, response was:", response.content, "\n\n\n")
        parsed = {
            "is_generic": False,
            "is_off_topic": False,
            "enhanced_query": state["user_query"],
            "reasoning": "parse error, using original query",
            "missing_aspects": [],
        }

    return {
        **state,
        "messages": [HumanMessage(content=state["user_query"])],
        "enhanced_query": parsed.get("enhanced_query", state["user_query"]),
        "enhancement_reasoning": parsed.get("reasoning", ""),
        "missing_aspects": parsed.get("missing_aspects", []),
    }