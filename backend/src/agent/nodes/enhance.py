from langchain_core.messages import HumanMessage, SystemMessage
from config import settings
from services.groq_client import llm
from agent.state import AgentState

ENHANCE_SYSTEM_PROMPT = """
You are a cybersecurity expert assistant. Your job is to analyze a user query and:
1. Determine if it is a GENERIC cybersecurity question (foundational concepts like 
   "what is XSS", "explain ransomware") or a SPECIFIC question requiring document lookup
   or a OFF-TOPIC question (not related to cybersecurity).
2. If SPECIFIC: rewrite the query in a very detailed way, adding relevant technical keywords, CVE references,
   attack/defense terminology to maximize vector search recall.
3. If GENERIC: mark it as generic (not off-topic), no enhancement needed.
4. If OFF-TOPIC: mark it as generic and as off-topic, and return the original query (the system will handle it later).

Definition: 
A generic question is one that can be answered with general cybersecurity knowledge, without needing
to reference specific documents. Examples of generic questions include:
- "What is a buffer overflow attack?"
- "How does a phishing attack work?"
- "What are common mitigations for DDoS attacks?"
A off-topic question is one that is not related to cybersecurity at all, such as:
- "What is the capital of France?"
- "How do I bake a cake?"

Exception: normal user interaction like:
- "Hi"
- "Thank you"
- "Can you help me?"
this should be classified as generic and not off-topic, to allow a friendly response.

Respond ONLY in this JSON format:
{
  "is_generic": true/false,
  "is_off_topic": true/false,
  "enhanced_query": "...",
  "reasoning": "...",
  "missing_aspects": []
}
"""

# Prompt per il secondo tentativo, quando l'evaluator ha già detto cosa manca
ENHANCE_RETRY_PROMPT = """
You are a cybersecurity expert assistant. A previous search attempt was insufficient.

Original query: {original_query}
Previous enhanced query: {previous_enhanced}
What was missing from retrieved documents: {missing_aspects}

Rewrite the query to target the missing aspects. Add different keywords,
synonyms, related attack techniques or standards (MITRE ATT&CK, CVE, OWASP).

Respond ONLY in this JSON format:
{
  "is_generic": false,
  "is_off_topic": false,
  "enhanced_query": "...",
  "reasoning": "...",
  "missing_aspects": []
}
"""

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
        "is_generic_cybersecurity": parsed.get("is_generic", False),
        "is_off_topic": parsed.get("is_off_topic", False),
        "enhanced_query": parsed.get("enhanced_query", state["user_query"]),
        "enhancement_reasoning": parsed.get("reasoning", ""),
        "missing_aspects": parsed.get("missing_aspects", []),
    }