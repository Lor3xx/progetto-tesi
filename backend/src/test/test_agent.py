# test/test_agent.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from agent.graph import rag_graph
from agent.state import AgentState

def run_query(query: str, label: str):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"Query: {query}")
    print('='*60)

    initial_state = AgentState(
        user_query=query,
        enhanced_query="",
        enhancement_reasoning="",
        retrieved_chunks=[],
        retrieved_image_chunks=[],
        eval_score=0.0,
        eval_reasoning="",
        missing_aspects=[],
        retry_count=0,
        draft_response="",
        final_response="",
        sources=[],
        images=[],
        is_generic_cybersecurity=False,
        is_off_topic=False,
        response_status="unknown",
        messages=[],
    )

    result = rag_graph.invoke(initial_state)

    print(f"Status        : {result['response_status']}")
    print(f"Is generic    : {result['is_generic_cybersecurity']}")
    print(f"Is off-topic  : {result['is_off_topic']}")
    print(f"Enhanced query: {result['enhanced_query']}")
    print(f"Eval score    : {result['eval_score']:.2f}")
    print(f"Retry count   : {result['retry_count']}")
    print(f"Sources       : {result['sources']}")
    print(f"Images found  : {len(result['images'])}")
    print(f"\nRESPONSE:\n{result['final_response']}")


if __name__ == "__main__":

    # 1. Domanda pertinente al documento caricato
    # → dovrebbe fare retrieve, trovare chunk, rispondere con fonti
    run_query(
        query="Adversarial Attacks on XAI",
        label="Domanda pertinente al documento"
    )

    # 2. Domanda generica cybersecurity
    # → is_generic=True, salta retrieve, risponde subito
    run_query(
        query="What is a buffer overflow attack?",
        label="Domanda generica cybersecurity"
    )

    # 3. Domanda fuori contesto, non cybersecurity
    # → retrieve non trova nulla sopra soglia → no_documents
    run_query(
        query="Dammi la ricetta della pizza",
        label="Domanda fuori contesto"
    )

    # 4. Domanda cybersecurity ma non coperta dal documento
    # → retrieve cerca ma non trova chunk pertinenti → no_documents
    run_query(
        query="Explain the internal architecture of the Mirai botnet malware",
        label="Domanda cybersecurity non nel documento"
    )