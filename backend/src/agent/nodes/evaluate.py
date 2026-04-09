import json
from agent.prompts import EVAL_RESPONSE_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState
from services.llm_client import llm_eval

def extract_text_content(response):
    content = response.content

    # Se è già stringa (vecchio comportamento)
    if isinstance(content, str):
        return content

    # Se è lista (Gemini)
    if isinstance(content, list):
        for block in content:
            if block.get("type") == "text":
                return block.get("text", "")

    return ""


def evaluate_node(state: AgentState) -> AgentState:
    user_content = (
        f"User query: {state['user_query']}\n\n"
        f"Generated response: {state['draft_response']}"
    )

    print("\nInvoking evaluate_node")
    response = llm_eval.invoke([
        SystemMessage(content=EVAL_RESPONSE_PROMPT),
        HumanMessage(content=user_content),
    ])

    try:
        raw_text = extract_text_content(response)
        clean = (raw_text.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = {"score": 0.0, "is_satisfactory": False, "is_complete": False, "is_accurate": False, "is_on_topic": False,
                  "reasoning": "parse error", "missing_aspects": []}

    return {
        **state,
        "eval_score": parsed.get("score", state["eval_score"]),
        "eval_reasoning": parsed.get("reasoning", ""),
        "missing_aspects": parsed.get("missing_aspects", []),
    }