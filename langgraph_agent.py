"""
langgraph_agent.py
------------------
LangGraph version of the Call Center AI Analyst agent.
Uses the SAME tools, prompt, LLM and vector store as utils.py.

Flow:
    START -> classify_intent --(general)--> general_answer -> END
                             --(data)-----> analyst --(final answer)--> END
                                               |
                                      (needs data)
                                               v
                                             tools -> check_tools --(ok / retries left)--> analyst
                                                          |
                                                          +--(too many failures)--> give_up -> END
                                                          +--(tool limit reached)--> wrap_up -> END

Called from utils.run_agent() when AGENT_ENGINE=langgraph.
"""

from typing import Annotated, Optional, TypedDict

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

# Everything below is reused from your existing utils.py
from utils import SYSTEM_PROMPT as BASE_PROMPT
from utils import TOOLS, set_vectorstore

# ---------------------------------------------------------------------------
# SETTINGS
# ---------------------------------------------------------------------------
SYSTEM = SystemMessage(
    content=BASE_PROMPT
    + """

Rules:
- Always call a tool to get numbers. Never guess or invent figures.
- metric must be exactly one of: aht, fcr, csat, adherence.
- period must look like Q1, Q2, Q3, Q4, Jan-2024 ... Dec-2024, or all.
- If a tool returns an error, fix the arguments and call it again.
- Compare numbers with targets carefully: FCR, CSAT and Adherence are above target only if the value is greater than the target; AHT meets target only if it is below 5.0 minutes.
- When a tool gives a gap vs target or vs team, quote it exactly. Never recompute it.
- State only facts that appear in tool results. Present explanations as possibilities ("may", "could"), not as facts.
- Do not give projected improvement numbers or timelines, and do not refer to data that is not in the database (call types, call recordings, scripts, reports).
- Do not use HTML tags such as <br>. Use plain Markdown."""
)

GENERAL_SYSTEM = SystemMessage(
    content=(
        "You are a friendly Call Center Analytics AI Analyst. "
        "Answer greetings and general questions briefly. "
        "If the user wants data, suggest questions about AHT, FCR, CSAT, "
        "adherence, individual agents, or Team A vs Team B."
    )
)

MAX_RETRIES = 2        # retries after a failed tool call (3 tries in total)
MAX_TOOL_ROUNDS = 6    # max tool batches per question (old agent used 8 iterations)
HISTORY_TURNS = 3      # past questions sent to the LLM (old memory kept 3 Q&A pairs)
RECURSION_LIMIT = 40   # last-resort safety stop

# A tool result starting with one of these counts as a failed call
ERROR_PREFIXES = (
    "error",
    "database error",
    "invalid",
    "metric is required",
    "could not get data",
)

# Words that clearly mean "this needs data"
DATA_KEYWORDS = [
    "aht", "fcr", "csat", "adherence", "kpi", "handle time", "resolution",
    "satisfaction", "call", "agent", "team", "performance", "trend",
    "q1", "q2", "q3", "q4", "rank", "below target", "above target",
    "ravi", "pooja", "arjun", "sneha", "vikram", "divya", "rahul",
    "kavya", "amit", "priya",
]


# ---------------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------------
class AnalystState(TypedDict):
    messages: Annotated[list, add_messages]  # conversation history
    intent: str                              # "data_query" or "general"
    error: Optional[str]                     # last tool error text
    retries: int                             # failed-tool retries used this turn
    rounds: int                              # tool batches used this turn


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return "".join(parts)
    return str(content)


def _current_turn(messages: list) -> list:
    """Messages after the latest user question."""
    last_human = -1
    for i, m in enumerate(messages):
        if m.type == "human":
            last_human = i
    return messages[last_human + 1:]


def _recent(messages: list, turns: int = HISTORY_TURNS) -> list:
    """Keep only the last few user turns (always starts at a user message)."""
    human_idx = [i for i, m in enumerate(messages) if m.type == "human"]
    if len(human_idx) <= turns:
        return messages
    return messages[human_idx[-turns]:]


def _is_tool_error(msg) -> bool:
    if msg.type != "tool":
        return False
    if getattr(msg, "status", None) == "error":
        return True
    return _text(msg.content).strip().lower().startswith(ERROR_PREFIXES)


# ---------------------------------------------------------------------------
# GRAPH
# ---------------------------------------------------------------------------
_checkpointer = MemorySaver()   # built-in conversation memory (one thread = one session)
_graph = None


def build_graph(llm):
    llm_with_tools = llm.bind_tools(TOOLS)

    # node 1: data question or small talk?
    def classify_intent(state: AnalystState):
        question = _text(state["messages"][-1].content).lower()

        if any(k in question for k in DATA_KEYWORDS):
            intent = "data_query"
        else:
            recent = _recent(state["messages"], 2)
            transcript = "\n".join(
                f"{m.type}: {_text(m.content)[:300]}"
                for m in recent
                if m.type in ("human", "ai") and _text(m.content).strip()
            )
            try:
                reply = llm.invoke(
                    "Classify the LAST user message. Reply with exactly one word.\n"
                    "data_query = needs call center data (KPIs, calls, agents, teams, "
                    "trends) or is a follow-up to such a question.\n"
                    "general = greeting, thanks, or a question about what you can do.\n\n"
                    f"{transcript}\n\nAnswer:"
                )
                label = _text(reply.content).strip().lower()
                intent = "general" if label.startswith("general") else "data_query"
            except Exception:
                intent = "data_query"   # LLM unavailable: the analyst node reports the error

        return {"intent": intent, "retries": 0, "rounds": 0, "error": None}

    # node 2: the LLM thinks and may call tools
    def analyst(state: AnalystState):
        prompt = [SYSTEM]
        if state.get("error"):
            prompt.append(
                SystemMessage(
                    content=(
                        f"Your previous tool call failed with: {state['error']}\n"
                        "Fix the arguments and call the tool again."
                    )
                )
            )
        last_err = None
        for _ in range(2):  # Groq sometimes fails on a tool call; try once more
            try:
                response = llm_with_tools.invoke(prompt + _recent(state["messages"]))
                return {"messages": [response]}
            except Exception as e:
                last_err = e
        return {
            "messages": [
                AIMessage(
                    content=(
                        "Sorry, the language model failed to respond "
                        f"({str(last_err)[:150]}). Please try again."
                    )
                )
            ]
        }

    # node 3: runs the tools; handle_tool_errors=True turns a crash into an error message
    tool_node = ToolNode(TOOLS, handle_tool_errors=True)

    # node 4: look at the tool results, count failures and rounds
    def check_tools(state: AnalystState):
        batch = []
        for m in reversed(state["messages"]):
            if m.type == "tool":
                batch.append(m)
            else:
                break
        errors = [m for m in batch if _is_tool_error(m)]
        update = {"rounds": state.get("rounds", 0) + 1, "error": None}
        if errors:
            update["error"] = _text(errors[-1].content)[:500]
            update["retries"] = state.get("retries", 0) + 1
        return update

    # node 5: stop politely
    def give_up(state: AnalystState):
        if state.get("error"):
            first_line = str(state["error"]).splitlines()[0]
            msg = (
                f"Sorry, I could not fetch that data after {MAX_RETRIES + 1} attempts. "
                f"Last error: {first_line} "
                "Please rephrase the question or check the database."
            )
        else:
            msg = (
                "Sorry, I needed too many steps to answer that. "
                "Please ask a more specific question."
            )
        return {"messages": [AIMessage(content=msg)], "error": None}

    # node 5b: tool limit reached -> answer from the data already gathered
    def wrap_up(state: AnalystState):
        turn = _current_turn(state["messages"])
        question = ""
        for m in reversed(state["messages"]):
            if m.type == "human":
                question = _text(m.content)
                break
        chunks = [
            _text(m.content)[:1500]
            for m in turn
            if m.type == "tool" and not _is_tool_error(m)
        ]
        data = "\n\n".join(chunks)[:7000]
        fallback = AIMessage(
            content=(
                "Sorry, I needed too many steps to answer that. "
                "Please ask a more specific question."
            )
        )
        if not data.strip():
            return {"messages": [fallback]}
        try:
            reply = llm.invoke(
                [
                    SYSTEM,
                    HumanMessage(
                        content=(
                            f"Question: {question}\n\n"
                            f"Tool results gathered so far:\n{data}\n\n"
                            "The tool limit has been reached. Answer the question now "
                            "using ONLY the results above. Do not invent numbers or causes."
                        )
                    ),
                ]
            )
            text = _text(reply.content).strip()
            return {"messages": [AIMessage(content=text)] if text else [fallback]}
        except Exception:
            return {"messages": [fallback]}

    # node 6: small talk, no tools
    def general_answer(state: AnalystState):
        plain = [
            m
            for m in _recent(state["messages"])
            if m.type == "human"
            or (m.type == "ai" and not getattr(m, "tool_calls", None) and _text(m.content).strip())
        ]
        try:
            return {"messages": [llm.invoke([GENERAL_SYSTEM] + plain)]}
        except Exception as e:
            return {
                "messages": [
                    AIMessage(
                        content=(
                            "Sorry, the language model failed to respond "
                            f"({str(e)[:150]}). Please try again."
                        )
                    )
                ]
            }

    # routers
    def route_after_classify(state: AnalystState):
        return "analyst" if state["intent"] == "data_query" else "general_answer"

    def route_after_analyst(state: AnalystState):
        last = state["messages"][-1]
        return "tools" if getattr(last, "tool_calls", None) else "end"

    def route_after_check(state: AnalystState):
        if state.get("error") and state.get("retries", 0) > MAX_RETRIES:
            return "give_up"
        if state.get("rounds", 0) >= MAX_TOOL_ROUNDS:
            return "wrap_up"
        return "analyst"

    builder = StateGraph(AnalystState)
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("analyst", analyst)
    builder.add_node("tools", tool_node)
    builder.add_node("check_tools", check_tools)
    builder.add_node("give_up", give_up)
    builder.add_node("wrap_up", wrap_up)
    builder.add_node("general_answer", general_answer)

    builder.add_edge(START, "classify_intent")
    builder.add_conditional_edges(
        "classify_intent", route_after_classify,
        {"analyst": "analyst", "general_answer": "general_answer"},
    )
    builder.add_conditional_edges(
        "analyst", route_after_analyst, {"tools": "tools", "end": END}
    )
    builder.add_edge("tools", "check_tools")
    builder.add_conditional_edges(
        "check_tools", route_after_check,
        {"analyst": "analyst", "give_up": "give_up", "wrap_up": "wrap_up"},
    )
    builder.add_edge("give_up", END)
    builder.add_edge("wrap_up", END)
    builder.add_edge("general_answer", END)

    return builder.compile(checkpointer=_checkpointer)


def get_graph(llm):
    global _graph
    if _graph is None:
        _graph = build_graph(llm)
    return _graph


def clear_langgraph_history(session_id: str):
    """Forget one chat session (used by utils.clear_history)."""
    try:
        _checkpointer.delete_thread(session_id)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# SAME INPUT / OUTPUT AS utils.run_agent()
# ---------------------------------------------------------------------------
def run_langgraph_agent(question: str, session_id: str, llm, vectorstore) -> dict:
    set_vectorstore(vectorstore)   # the search_knowledge_base tool reads this
    graph = get_graph(llm)
    config = {
        "configurable": {"thread_id": session_id},
        "recursion_limit": RECURSION_LIMIT,
    }

    try:
        result = graph.invoke({"messages": [HumanMessage(content=question)]}, config)
    except GraphRecursionError:
        clear_langgraph_history(session_id)   # avoid a half-finished turn in memory
        return {
            "answer": "Sorry, I got stuck on that question. Please try rephrasing it.",
            "sources": [],
            "tools_used": [],
            "session_id": session_id,
        }

    turn = _current_turn(result["messages"])

    tools_used = []
    for m in turn:
        if m.type == "ai":
            for call in getattr(m, "tool_calls", None) or []:
                if call["name"] not in tools_used:
                    tools_used.append(call["name"])

    last_ai = next((m for m in reversed(turn) if isinstance(m, AIMessage)), None)
    answer = _text(last_ai.content).strip() if last_ai else ""
    if not answer:
        answer = "I could not generate an answer. Please try again."

    sources = []
    if vectorstore is not None:
        for doc in vectorstore.similarity_search(question, k=2):
            sources.append({
                "content": doc.page_content[:300] + "...",
                "doc_type": doc.metadata.get("type", "document"),
            })

    return {
        "answer": answer,
        "sources": sources,
        "tools_used": tools_used,
        "session_id": session_id,
    }
