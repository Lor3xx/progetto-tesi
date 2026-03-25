import json
from langchain_core.messages import HumanMessage
from services.groq_client import llm_eval
from agent.state import AgentState

CLASSIFY_PROMPT = """
You are a cybersecurity expert assistant. Your job is to analyze a user query and:
1. Determine if it is a GENERIC cybersecurity question (foundational concepts like 
   "what is XSS", "explain ransomware") or a SPECIFIC question requiring document lookup
   or a OFF-TOPIC question (not related to cybersecurity).
2. If SPECIFIC: rewrite the query adding relevant technical keywords, CVE references,
   attack/defense terminology to maximize vector search recall.
3. If GENERIC: mark it as generic, no enhancement needed.
4. If OFF-TOPIC: mark it as generic and return the original query (the system will handle it later).

- "generic_cyber": general cybersecurity question answerable from common knowledge
  (e.g. "what is XSS", "explain ransomware", "how does a firewall work")
- "specific_cyber": question requiring lookup in specific cybersecurity documents
  (e.g. "what does our policy say about...", "find vulnerabilities in...", specific CVEs)
- "off_topic": anything unrelated to cybersecurity

Respond ONLY in this JSON format, no markdown, no backticks:
{{
  "category": "generic_cyber" | "specific_cyber" | "off_topic",
  "reasoning": "..."
}}
"""

def classify_node(state: AgentState) -> AgentState:
    response = llm_eval.invoke([
        HumanMessage(content=f"{CLASSIFY_PROMPT}\n\nQuery: {state['user_query']}")
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
        "response_status": category,
    }