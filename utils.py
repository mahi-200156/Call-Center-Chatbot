import os
import sqlite3
from collections import deque
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor

load_dotenv()

# CONVERSATION MEMORY
_memory: dict = {}

def get_history(session_id: str) -> list:
    if session_id not in _memory:
        _memory[session_id] = deque(maxlen=6)
    return list(_memory[session_id])

def save_to_history(session_id: str, human: str, ai: str):
    if session_id not in _memory:
        _memory[session_id] = deque(maxlen=6)
    _memory[session_id].append(f"Human: {human}")
    _memory[session_id].append(f"AI: {ai}")

def clear_history(session_id: str):
    if session_id in _memory:
        _memory[session_id].clear()



def init_llm():
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )

def init_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

def load_vectorstore(embeddings):
    return FAISS.load_local(
        "vectorstore_cc", embeddings,
        allow_dangerous_deserialization=True
    )

def get_db():
    conn = sqlite3.connect("cc_database.db")
    conn.row_factory = sqlite3.Row
    return conn


_vs = None
def set_vectorstore(vs): global _vs; _vs = vs


# AGENT TOOLS

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search call center knowledge base using semantic similarity.
    Use for: KPI definitions, monthly team summaries, agent profiles,
    general performance narratives.
    Input: search query string.
    """
    if _vs is None:
        return "Knowledge base not loaded."
    docs = _vs.similarity_search(query, k=4)
    return "\n\n---\n\n".join(
        f"[{d.metadata.get('type','doc')}]\n{d.page_content}" for d in docs
    )


@tool
def get_agent_metrics(agent_name: str, metric: str = "all", period: str = "all") -> str:
    """
    Get KPI data for a specific agent from the database.
    Use for precise numerical questions about one agent.
    Args:
        agent_name: partial name match e.g. 'Ravi' finds 'Ravi Sharma'
        metric: 'aht', 'fcr', 'csat', 'adherence', or 'all'
        period: month like 'Jan-2024', quarter 'Q1','Q2','Q3','Q4', or 'all'
    """
    QUARTERS = {
        "Q1":["Jan-2024","Feb-2024","Mar-2024"],
        "Q2":["Apr-2024","May-2024","Jun-2024"],
        "Q3":["Jul-2024","Aug-2024","Sep-2024"],
        "Q4":["Oct-2024","Nov-2024","Dec-2024"]
    }

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM performance WHERE LOWER(agent_name) LIKE LOWER(?) ORDER BY rowid",
        (f"%{agent_name}%",)
    ).fetchall()
    conn.close()

    if not rows:
        return (f"No agent found matching '{agent_name}'. "
                "Agents: Ravi Sharma, Pooja Mehta, Arjun Kumar, Sneha Iyer, "
                "Vikram Nair, Divya Patel, Rahul Joshi, Kavya Menon, Amit Gupta, Priya Reddy")

    if period.upper() in QUARTERS:
        rows = [r for r in rows if r["month_year"] in QUARTERS[period.upper()]]
    elif period.lower() != "all":
        rows = [r for r in rows if r["month_year"].lower() == period.lower()]

    if not rows:
        return f"No data for {agent_name} in period '{period}'"

    name = rows[0]["agent_name"]

    if metric.lower() == "all":
        header = f"{'Month':<12} {'AHT':>7} {'FCR':>7} {'CSAT':>7} {'Adh':>7} {'Calls':>7}"
        sep = "-" * 52
        lines = [f"{r['month_year']:<12} {r['aht']:>6.1f}m {r['fcr']:>6.1f}% {r['csat']:>6.1f}% {r['adherence']:>6.1f}% {r['calls_handled']:>7}" for r in rows]
        return f"Performance for {name}:\n{header}\n{sep}\n" + "\n".join(lines)
    else:
        col = metric.lower()
        lines = [f"  {r['month_year']}: {r[col]}" for r in rows]
        return f"{name} — {metric.upper()} trend:\n" + "\n".join(lines)


@tool
def get_team_comparison(period: str = "all") -> str:
    """
    Compare Team A vs Team B on all KPIs.
    Args:
        period: 'Q1','Q2','Q3','Q4', specific month like 'Jun-2024', or 'all'
    """
    QUARTERS = {
        "Q1":["Jan-2024","Feb-2024","Mar-2024"],
        "Q2":["Apr-2024","May-2024","Jun-2024"],
        "Q3":["Jul-2024","Aug-2024","Sep-2024"],
        "Q4":["Oct-2024","Nov-2024","Dec-2024"]
    }

    conn = get_db()

    if period.upper() in QUARTERS:
        months = QUARTERS[period.upper()]
        ph = ",".join("?"*len(months))
        rows = conn.execute(f"""
            SELECT team, ROUND(AVG(aht),2) a, ROUND(AVG(fcr),1) f,
                   ROUND(AVG(csat),1) c, ROUND(AVG(adherence),1) d, SUM(calls_handled) t
            FROM performance WHERE month_year IN ({ph}) GROUP BY team
        """, months).fetchall()
    elif period.lower() == "all":
        rows = conn.execute("""
            SELECT team, ROUND(AVG(aht),2) a, ROUND(AVG(fcr),1) f,
                   ROUND(AVG(csat),1) c, ROUND(AVG(adherence),1) d, SUM(calls_handled) t
            FROM performance GROUP BY team
        """).fetchall()
    else:
        rows = conn.execute("""
            SELECT team, ROUND(AVG(aht),2) a, ROUND(AVG(fcr),1) f,
                   ROUND(AVG(csat),1) c, ROUND(AVG(adherence),1) d, SUM(calls_handled) t
            FROM performance WHERE month_year=? GROUP BY team
        """, (period,)).fetchall()

    conn.close()

    if not rows:
        return f"No data for period: {period}"

    td = {r["team"]: r for r in rows}
    ta, tb = td.get("Team A",{}), td.get("Team B",{})

    out  = f"Team Comparison — {period}\n"
    out += f"{'Metric':<20} {'Team A':>10} {'Team B':>10} {'Target':>12}\n"
    out += "-"*55 + "\n"
    out += f"{'AHT (min)':<20} {str(ta.get('a','N/A')):>10} {str(tb.get('a','N/A')):>10} {'< 5.0':>12}\n"
    out += f"{'FCR (%)':<20} {str(ta.get('f','N/A')):>10} {str(tb.get('f','N/A')):>10} {'> 80%':>12}\n"
    out += f"{'CSAT (%)':<20} {str(ta.get('c','N/A')):>10} {str(tb.get('c','N/A')):>10} {'> 85%':>12}\n"
    out += f"{'Adherence (%)':<20} {str(ta.get('d','N/A')):>10} {str(tb.get('d','N/A')):>10} {'> 90%':>12}\n"
    out += f"{'Total Calls':<20} {str(ta.get('t','N/A')):>10} {str(tb.get('t','N/A')):>10}\n"
    return out


@tool
def get_top_bottom_agents(metric: str, n: int = 3, period: str = "all", rank: str = "top") -> str:
    """
    Get top or bottom N agents for a KPI.
    Use for ranking and leaderboard questions.
    Args:
        metric: 'aht', 'fcr', 'csat', or 'adherence'
        n: number of agents (default 3)
        period: 'Q1','Q2','Q3','Q4', month, or 'all'
        rank: 'top' for best performers, 'bottom' for worst
    """
    QUARTERS = {
        "Q1":["Jan-2024","Feb-2024","Mar-2024"],
        "Q2":["Apr-2024","May-2024","Jun-2024"],
        "Q3":["Jul-2024","Aug-2024","Sep-2024"],
        "Q4":["Oct-2024","Nov-2024","Dec-2024"]
    }

    # AHT: lower=better, so top performers = lowest AHT
    order = ("ASC" if rank=="top" else "DESC") if metric.lower()=="aht" else ("DESC" if rank=="top" else "ASC")

    conn = get_db()
    if period.upper() in QUARTERS:
        months = QUARTERS[period.upper()]
        ph = ",".join("?"*len(months))
        rows = conn.execute(f"""
            SELECT agent_name, team, ROUND(AVG({metric}),2) v
            FROM performance WHERE month_year IN ({ph})
            GROUP BY agent_name,team ORDER BY v {order} LIMIT ?
        """, (*months, n)).fetchall()
    elif period.lower() == "all":
        rows = conn.execute(f"""
            SELECT agent_name, team, ROUND(AVG({metric}),2) v
            FROM performance GROUP BY agent_name,team ORDER BY v {order} LIMIT ?
        """, (n,)).fetchall()
    else:
        rows = conn.execute(f"""
            SELECT agent_name, team, ROUND(AVG({metric}),2) v
            FROM performance WHERE month_year=?
            GROUP BY agent_name,team ORDER BY v {order} LIMIT ?
        """, (period, n)).fetchall()
    conn.close()

    if not rows:
        return f"No data for {metric} in {period}"

    unit = "min" if metric.lower()=="aht" else "%"
    label = {"aht":"AHT","fcr":"FCR","csat":"CSAT","adherence":"Adherence"}.get(metric.lower(), metric)
    out = f"{'Top' if rank=='top' else 'Bottom'} {n} agents — {label} — {period}:\n"
    for i, r in enumerate(rows, 1):
        out += f"  {i}. {r['agent_name']} ({r['team']}): {r['v']} {unit}\n"
    return out


@tool
def calculate_metric_change(agent_or_team: str, metric: str,
                             from_period: str, to_period: str) -> str:
    """
    Calculate % change in a KPI between two periods for an agent or team.
    Use for trend analysis and MoM/QoQ change questions.
    Args:
        agent_or_team: agent name (partial) OR 'Team A' / 'Team B'
        metric: 'aht', 'fcr', 'csat', or 'adherence'
        from_period: start period e.g. 'Jan-2024' or 'Q1'
        to_period: end period e.g. 'Dec-2024' or 'Q4'
    """
    QUARTERS = {
        "Q1":["Jan-2024","Feb-2024","Mar-2024"],
        "Q2":["Apr-2024","May-2024","Jun-2024"],
        "Q3":["Jul-2024","Aug-2024","Sep-2024"],
        "Q4":["Oct-2024","Nov-2024","Dec-2024"]
    }

    conn = get_db()

    def get_val(period):
        is_team = "team" in agent_or_team.lower()
        team_name = "Team A" if "a" in agent_or_team.lower() else "Team B"

        if period.upper() in QUARTERS:
            months = QUARTERS[period.upper()]
            ph = ",".join("?"*len(months))
            if is_team:
                r = conn.execute(f"SELECT AVG({metric}) FROM performance WHERE month_year IN ({ph}) AND team=?", (*months,team_name)).fetchone()
            else:
                r = conn.execute(f"SELECT AVG({metric}) FROM performance WHERE month_year IN ({ph}) AND LOWER(agent_name) LIKE LOWER(?)", (*months,f"%{agent_or_team}%")).fetchone()
        else:
            if is_team:
                r = conn.execute(f"SELECT AVG({metric}) FROM performance WHERE month_year=? AND team=?", (period,team_name)).fetchone()
            else:
                r = conn.execute(f"SELECT AVG({metric}) FROM performance WHERE month_year=? AND LOWER(agent_name) LIKE LOWER(?)", (period,f"%{agent_or_team}%")).fetchone()
        return r[0] if r and r[0] else None

    fv = get_val(from_period)
    tv = get_val(to_period)
    conn.close()

    if fv is None or tv is None:
        return f"Could not get data for '{agent_or_team}' — check name/period."

    change = round(tv - fv, 2)
    pct = round((change/fv)*100, 1) if fv else 0
    unit = "min" if metric.lower()=="aht" else "%"

    if metric.lower() == "aht":
        sentiment = "WORSE (AHT increased)" if change > 0 else "BETTER (AHT decreased)"
    else:
        sentiment = "BETTER" if change > 0 else "WORSE"

    return (
        f"{metric.upper()} change for {agent_or_team}:\n"
        f"  {from_period}: {round(fv,2)} {unit}\n"
        f"  {to_period}:   {round(tv,2)} {unit}\n"
        f"  Change: {'+' if change>0 else ''}{change} ({pct:+.1f}%)\n"
        f"  {sentiment}"
    )


# AGENT RUNNER

TOOLS = [
    search_knowledge_base,
    get_agent_metrics,
    get_team_comparison,
    get_top_bottom_agents,
    calculate_metric_change,
]

SYSTEM_PROMPT = """You are an expert Call Center Analytics AI Analyst with access to 2024 performance data.

KPI Targets:
- AHT (Average Handle Time): < 5.0 minutes — LOWER is better
- FCR (First Call Resolution): > 80%        — HIGHER is better
- CSAT (Customer Satisfaction): > 85%       — HIGHER is better
- Adherence (Schedule): > 90%               — HIGHER is better

Data: Jan-2024 to Dec-2024, 10 agents, Team A (Mumbai) and Team B (Bangalore).

Use the available tools to get accurate data. Always base your analysis on actual numbers.
Give concise, actionable insights with specific values."""


def run_agent(question: str, session_id: str, llm, vectorstore: FAISS) -> dict:
    """
    Run the ReAct agent on a question.

    ReAct loop:
      Thought → which tool do I need?
      Action  → call the tool
      Observation → what did it return?
      ... repeat until enough data ...
      Final Answer → generate analysis
    """
    set_vectorstore(vectorstore)

    history = get_history(session_id)
    history_str = "\n".join(history) if history else "No previous conversation."

    # ReAct prompt — works with Llama/Groq
    prompt_template = """You are an expert Call Center Analytics AI Analyst.

KPI Targets: AHT<5.0min (lower=better) | FCR>80% (higher=better) | CSAT>85% (higher=better) | Adherence>90% (higher=better)
Data period: Jan-2024 to Dec-2024 | Teams: Team A (Mumbai), Team B (Bangalore) | 10 agents

Previous conversation:
{history}

You have access to the following tools:
{tools}

Use this format STRICTLY:
Question: the input question
Thought: think about what tool to use
Action: tool name (must be one of [{tool_names}])
Action Input: input to the tool
Observation: tool result
... (repeat Thought/Action/Observation as needed)
Thought: I have enough information to answer
Final Answer: your complete analysis

Question: {input}
{agent_scratchpad}"""

    from langchain_core.prompts import PromptTemplate
    prompt = PromptTemplate.from_template(prompt_template).partial(history=history_str)

    agent = create_react_agent(llm=llm, tools=TOOLS, prompt=prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=TOOLS,
        verbose=True,
        max_iterations=8,
        handle_parsing_errors=True,
        return_intermediate_steps=True
    )

    result = executor.invoke({"input": question})
    answer = result["output"]

    tools_used = []
    for step in result.get("intermediate_steps", []):
        t = step[0].tool if hasattr(step[0], "tool") else str(step[0])
        if t not in tools_used:
            tools_used.append(t)

    save_to_history(session_id, question, answer)

    sources = []
    if _vs:
        for doc in _vs.similarity_search(question, k=2):
            sources.append({
                "content": doc.page_content[:300] + "...",
                "doc_type": doc.metadata.get("type", "document")
            })

    return {
        "answer": answer,
        "sources": sources,
        "tools_used": tools_used,
        "session_id": session_id
    }