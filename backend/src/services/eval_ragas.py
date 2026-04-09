from http import client
import os
from pathlib import Path
import sys
from uuid import uuid4

import instructor

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datasets import Dataset

from agent.graph import build_graph
from services.llm_client import llm, embeddings
from agent.state import AgentState
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy

    
def run_graph(graph, query):

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
        messages=[],
        query_category="unknown",
        response_status="unknown",
    )

    thread_id = str(uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    result = graph.invoke(initial_state, config=config)

    return {
        "question": query,
        "answer": result["final_response"],
        "contexts": [s["content"] for s in result.get("sources", [])],
    }


def build_dataset(graph, queries):
    rows = []

    for q in queries:
        rows.append(run_graph(graph, q))

    return Dataset.from_list(rows)

from groq import Groq
from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory
from sentence_transformers import SentenceTransformer

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)
llm_metric = llm_factory("llama-3.3-70b-versatile", provider="groq", client=client)

embedding_metric = SentenceTransformer("all-MiniLM-L6-v2")


def run_ragas_eval(dataset):
    return evaluate(
        dataset,
        metrics=[
            Faithfulness(llm=llm_metric), 
            AnswerRelevancy(llm=llm_metric, embeddings=embedding_metric),
        ],
        llm=llm_metric,
    )


if __name__ == "__main__":
    graph = build_graph(checkpointer=False)

    queries = [
        "Adversarial Attacks on XAI",
        "Context-Aware Phishing Email Detection"
    ]

    dataset = build_dataset(graph, queries)
    results = run_ragas_eval(dataset)

    print(results)