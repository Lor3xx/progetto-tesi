from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage  
from agent.state import AgentState
from agent.nodes.enhance import enhance_node
from agent.nodes.retrieve import retrieve_node
from agent.nodes.respond import respond_node
from agent.nodes.evaluate import evaluate_node
from config import settings


# --- Funzioni di routing ---

def route_after_enhance(state: AgentState) -> str:
    """Dopo enhance: se generica o fuori contensto vai a rispondere, altrimenti recupera documenti."""
    if state["is_generic_cybersecurity"] or state["is_off_topic"]:
        return "respond"
    return "retrieve"


def route_after_retrieve(state: AgentState) -> str:
    """
    Dopo retrieve: se ci sono chunk sopra soglia genera la risposta,
    altrimenti termina subito senza retry (il filtro score è già nel retriever).
    """
    has_chunks = (
        len(state["retrieved_chunks"]) > 0 or
        len(state["retrieved_image_chunks"]) > 0
    )
    if has_chunks:
        return "respond"
    return "no_documents"


def route_after_respond(state: AgentState) -> str:
    if state["is_generic_cybersecurity"] or state["is_off_topic"]:
        return "finalize"   # salta evaluate
    return "evaluate"


def route_after_evaluate(state: AgentState) -> str:
    """
    Dopo evaluate:
    - risposta ok → finalizza
    - risposta insufficiente e retry disponibili → torna a enhance
    - retry esauriti → risposta parziale
    """
    if state["eval_score"] >= settings.min_eval_score:
        return "finalize"
    if state["retry_count"] < settings.max_retries:
        return "enhance"
    return "partial"


# --- Nodi terminali ---

def no_documents_node(state: AgentState) -> AgentState:
    """Termina il flusso comunicando assenza di documenti pertinenti."""
    return {
        **state,
        "final_response": (
            "I could not find any relevant documents to answer your question. "
            "The topic may not be covered in the loaded knowledge base."
        ),
        "response_status": "unknown",
        "messages": [AIMessage(content=(
            "I could not find any relevant documents to answer your question. "
            "The topic may not be covered in the loaded knowledge base."
        ))],
    }


def finalize_node(state: AgentState) -> AgentState:
    """Promuove la bozza a risposta finale."""
    return {
        **state,
        "final_response": state["draft_response"],
        "response_status": "complete",
        "messages": [AIMessage(content=state["draft_response"])],
    }


def partial_node(state: AgentState) -> AgentState:
    """
    Retry esauriti ma c'è una bozza: restituisce risposta parziale con disclaimer.
    """
    disclaimer = (
        "\n\n---\n"
        "⚠️ Note: this response may be incomplete. "
        "Not all aspects of your question could be fully covered "
        "by the available documents."
    )
    return {
        **state,
        "final_response": state["draft_response"] + disclaimer,
        "response_status": "partial",
        "messages": [AIMessage(content=state["draft_response"] + disclaimer)],
    }


# --- Costruzione del grafo ---

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Registra i nodi
    graph.add_node("enhance", enhance_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("respond", respond_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("no_documents", no_documents_node)
    graph.add_node("finalize", finalize_node)
    graph.add_node("partial", partial_node)

    # Entry point
    graph.set_entry_point("enhance")

    # Edge condizionale dopo enhance
    graph.add_conditional_edges(
        "enhance",
        route_after_enhance,
        {
            "respond": "respond",
            "retrieve": "retrieve",
        }
    )

    # Edge condizionale dopo retrieve
    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "respond": "respond",
            "no_documents": "no_documents",
        }
    )

    # Edge condizionale dopo respond
    graph.add_conditional_edges(
        "respond",
        route_after_respond,
        {
            "evaluate": "evaluate",
            "finalize": "finalize",
        }
    )

    # Edge condizionale dopo evaluate
    graph.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "finalize": "finalize",
            "enhance": "enhance",
            "partial": "partial",
        }
    )

    # Tutti i nodi terminali vanno a END
    graph.add_edge("no_documents", END)
    graph.add_edge("finalize", END)
    graph.add_edge("partial", END)

    memory = SqliteSaver.from_conn_string(settings.sqlite_path)
    return graph.compile(checkpointer=memory)


# Istanza globale compilata, importata dalle route FastAPI
rag_graph = build_graph()