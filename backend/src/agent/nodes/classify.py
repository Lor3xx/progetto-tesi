from agent.state import AgentState
from agent.prompts import CLASSIFY_SYSTEM_PROMPT
from langchain_core.messages import HumanMessage, SystemMessage
from services.llm_client import llm
from pydantic import BaseModel
import json

class ClassifyOutput(BaseModel):
    is_off_topic: bool
    is_specific: bool
    classify_reasoning: str

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

def classify_node(state: AgentState) -> AgentState:

    structured_llm = llm.with_structured_output(ClassifyOutput)

    print("\nInvoking classify_node")
    response = llm.invoke([
        SystemMessage(content=CLASSIFY_SYSTEM_PROMPT),
        *state["messages"],
        HumanMessage(content=state["user_query"]),
    ])
    print(f"LLM response for classification: {response}")
    try:
        raw_text = extract_text_content(response)

        clean = (raw_text.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = {"is_off_topic": False, "is_specific": False, "classify_reasoning": "parse error"}

    print(f"Parsed classification output: {parsed}")
    return {
        **state,
        "is_off_topic": parsed["is_off_topic"],
        "is_specific": parsed["is_specific"],
        "classify_reasoning": parsed["classify_reasoning"],
    }