import json
from langchain_core.messages import HumanMessage, SystemMessage
from agent.state import AgentState
from services.groq_client import llm_eval

EVAL_RESPONSE_PROMPT = """
You are evaluating a generated response against a user query.

Query: {query}
Response: {response}

Evaluate if the response fully and accurately answers the query.
Respond ONLY in this JSON format:
{
  "score": 0.0-1.0,
  "is_satisfactory": true/false,
  "is_complete": true/false,
  "is_accurate": true/false,
  "is_on_topic": true/false,
  "reasoning": "...",
  "missing_aspects": ["..."]
}
"""

def evaluate_node(state: AgentState) -> AgentState:
    user_content = (
        f"User query: {state['user_query']}\n\n"
        f"Generated response: {state['draft_response']}"
    )

    response = llm_eval.invoke([
        SystemMessage(content=EVAL_RESPONSE_PROMPT),
        HumanMessage(content=user_content),
    ])

    try:
        clean = (response.content.strip()
                 .removeprefix("```json").removeprefix("```")
                 .removesuffix("```").strip())
        parsed = json.loads(clean)
    except json.JSONDecodeError:
        parsed = {"score": 0.0, "is_satisfactory": False, "is_complete": False, "is_accurate": False, "is_on_topic": False,
                  "reasoning": "parse error", "missing_aspects": []}

    return {
        **state,
        "eval_score": parsed.get("score", 0.0),
        "eval_reasoning": parsed.get("reasoning", ""),
        "missing_aspects": parsed.get("missing_aspects", []),
    }