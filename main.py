from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import traceback

from schemas import ChatRequest, ChatResponse, Source
from utils import (
    init_llm, init_embeddings, load_vectorstore,
    run_agent, clear_history, get_db
)

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Call Center AI Analyst")
    app.state.llm        = init_llm()
    print("Groq LLM ready")
    app.state.embeddings = init_embeddings()
    print("HuggingFace embeddings ready ")
    app.state.vs         = load_vectorstore(app.state.embeddings)
    print("Vector store loaded")
    print("Server ready!\n")
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Call Center AI Analyst ",
    description="""
    AI-powered call center analytics using Groq (Llama 3.3) + HuggingFace.

    **5 Agent Tools:**
    - search_knowledge_base → semantic RAG search
    - get_agent_metrics → SQL query per agent
    - get_team_comparison → Team A vs Team B
    - get_top_bottom_agents → rankings
    - calculate_metric_change → trend analysis

    **KPI Targets:** AHT <5.0min | FCR >80% | CSAT >85% | Adherence >90%
    **Data:** Jan–Dec 2024, 10 agents, 2 teams
    """,
    version="1.0.0"
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest):
    """
    Ask any question about call center performance.

    Try:
    - 'What was Team A AHT trend in 2024?'
    - 'Who has the worst FCR in Q3?'
    - 'Compare Team A vs Team B for the full year'
    - 'Show me Kavya Menon complete performance'
    - 'Which agents are below CSAT target?'
    - 'How did FCR change from Q1 to Q4?'
    """
    try:
        result = run_agent(
            question=request.question,
            session_id=request.session_id,
            llm=app.state.llm,
            vectorstore=app.state.vs
        )
        return ChatResponse(
            answer=result["answer"],
            sources=[Source(**s) for s in result["sources"]],
            session_id=result["session_id"],
            tools_used=result["tools_used"]
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear_history", tags=["Chat"])
def clear(session_id: str = "default"):
    """Clear conversation memory for a session."""
    clear_history(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/agents", tags=["Data"])
def list_agents():
    """List all agents in the system."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM agents ORDER BY team, name").fetchall()
    conn.close()
    return {"agents": [dict(r) for r in rows]}


@app.get("/health", tags=["System"])
def health():
    return {
        "status": "healthy",
        "llm": "groq/llama-3.3-70b-versatile",
        "embeddings": "HuggingFace/all-MiniLM-L6-v2",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)