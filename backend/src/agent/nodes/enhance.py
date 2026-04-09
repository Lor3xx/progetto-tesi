import json

from agent.prompts import ENHANCE_RETRY_PROMPT, ENHANCE_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from services.llm_client import llm_enhance
from agent.state import AgentState
class EnhanceOutput(BaseModel):
    enhanced_query: str
    enhancement_reasoning: str
    missing_aspects: list[str]

def extract_text_content(response):
    content = response.content

    # Se è già stringa (vecchio comportamento)
    if isinstance(content, str):
        json_start = content.find("{")
        json_end = content.rfind("}") + 1

        clean = content[json_start:json_end]
        return clean

    # Se è lista (Gemini)
    if isinstance(content, list):
        for block in content:
            if block.get("type") == "text":
                return block.get("text", "")

    return ""


def enhance_node(state: AgentState) -> AgentState:

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

    print("\nInvoking enhance_node")
    response = llm_enhance.invoke(messages)

    print(f"LLM response for enhancement: {response}")
    try:
        raw_text = extract_text_content(response)

        clean = (raw_text.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = {"enhanced_query": state["user_query"], "enhancement_reasoning": "parse error", "missing_aspects": []}
    print(f"Parsed enhancement output: {parsed}")

    return {
        **state,
        "enhanced_query": parsed["enhanced_query"],
        "enhancement_reasoning": parsed["enhancement_reasoning"],
        "missing_aspects": parsed["missing_aspects"],
    }