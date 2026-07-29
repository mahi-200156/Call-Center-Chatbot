
import streamlit as st
import time
import os
# from dotenv import load_dotenv

# load_dotenv()

st.set_page_config(
    page_title="Call Center AI Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def load_all():
    from langchain_groq import ChatGroq
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
    from utils import set_vectorstore

    groq_key = (
        st.secrets.get("GROQ_API_KEY", None)
        or os.getenv("GROQ_API_KEY")
    )
    
    # groq_key = os.getenv("GROQ_API_KEY")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=groq_key
    )

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    vs = FAISS.load_local(
        "vectorstore_cc",
        embeddings,
        allow_dangerous_deserialization=True
    )

    set_vectorstore(vs)

    return llm, vs


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("📊 CC AI Analyst")
    st.caption("Powered by Groq + FAISS")
    st.divider()

    # KPI targets display
    st.subheader("🎯 KPI Targets")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("AHT", "< 5.0 min", delta="lower=better",
                  delta_color="inverse")
        st.metric("FCR", "> 80%", delta="higher=better")
    with col2:
        st.metric("CSAT", "> 85%", delta="higher=better")
        st.metric("Adherence", "> 90%", delta="higher=better")

    st.divider()
    st.subheader("💡 Try These")

    examples = [
        "Who are top 3 agents by FCR?",
        "Why is Vikram Nair underperforming?",
        "Compare Team A vs Team B",
        "Show Kavya Menon full performance",
        "Which agents are below CSAT target?",
        "How did FCR change Q1 to Q4?",
        "What is AHT and why does it matter?",
        "Who needs coaching most urgently?",
        "Best performing agents overall",
        "Show Team B Q3 performance"
    ]

    for ex in examples:
        if st.button(ex, use_container_width=True,
                     key=f"ex_{ex[:20]}"):
            st.session_state.sidebar_q = ex

    st.divider()

    if st.button("🗑️ Clear Chat History",
                 use_container_width=True):
        st.session_state.cc_messages = []
        from utils import clear_history
        clear_history("streamlit")
        st.success("Cleared!")

    st.divider()
    st.subheader("📈 Data Overview")
    st.caption("10 agents | 2 teams")
    st.caption("Jan 2024 — Dec 2024")
    st.caption("5 KPIs tracked monthly")
    st.caption("600+ data points total")

    st.divider()
    st.subheader("🔬 RAGAS Evaluation")
    st.caption("Faithfulness:      0.89 ✅")
    st.caption("Answer Relevancy:  0.86 ✅")
    st.caption("Context Precision: 0.81 ✅")
    st.caption("*(update with your actual scores)*")

with st.spinner("Loading AI models — please wait..."):
    llm, vs = load_all()

st.title("📊 Call Center AI Analyst")
st.caption(
    "Ask any question about agent performance, "
    "KPIs, trends, or team comparisons"
)

# Tabs for Chat and Agent Info
tab1, tab2 = st.tabs(["💬 Chat", "ℹ️ How It Works"])

with tab2:
    st.subheader("How This Agent Works")
    st.markdown("""
This is a **ReAct Agent** with 5 domain-specific tools.
The AI decides which tools to call based on your question.

| Your Question | Tool Used |
|---|---|
| "What is AHT?" | `search_knowledge_base` (RAG) |
| "Show Ravi's metrics" | `get_agent_metrics` (SQL) |
| "Team A vs Team B" | `get_team_comparison` (SQL) |
| "Who has worst FCR?" | `get_top_bottom_agents` (SQL) |
| "Did FCR improve Q1→Q4?" | `calculate_metric_change` (SQL+Math) |
| "Why is agent underperforming?" | **3 tools combined** |

The `tools_used` field in each response shows exactly
which tools were called. This is what makes it an
**agent** rather than just a chatbot.

**KPI Direction Logic (embedded in tools):**
- AHT → lower is better → rankings sort ascending for "top"
- FCR, CSAT, Adherence → higher is better → sort descending

This domain knowledge came from 2 years of working with
real call center data — it's baked into the tool logic.
    """)

    st.subheader("Agents in the System")
    agents_data = {
        "Team A (Mumbai)": [
            "Ravi Sharma", "Pooja Mehta",
            "Vikram Nair", "Rahul Joshi", "Amit Gupta"
        ],
        "Team B (Bangalore)": [
            "Arjun Kumar", "Sneha Iyer",
            "Divya Patel", "Kavya Menon", "Priya Reddy"
        ]
    }
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Team A — Mumbai (Lead: Vandana Singh)**")
        for name in agents_data["Team A (Mumbai)"]:
            st.write(f"• {name}")
    with col2:
        st.write("**Team B — Bangalore (Lead: Rahul Verma)**")
        for name in agents_data["Team B (Bangalore)"]:
            st.write(f"• {name}")


with tab1:
    # Initialize chat history
    if "cc_messages" not in st.session_state:
        st.session_state.cc_messages = []

    # Welcome message on first load
    if not st.session_state.cc_messages:
        with st.chat_message("assistant"):
            st.markdown("""
👋 Hello! I'm your **Call Center AI Analyst**.

I have access to **12 months of performance data**
(Jan–Dec 2024) for **10 agents** across
**Team A (Mumbai)** and **Team B (Bangalore)**.

I can help with:
- 📊 **Agent performance** — any KPI, any time period
- 🏆 **Rankings** — top/bottom performers
- 📈 **Trends** — how metrics changed over time
- ⚖️ **Team comparison** — Team A vs Team B
- 🔍 **Root cause** — why an agent is underperforming
- 📚 **KPI definitions** — what metrics mean and targets

Try: *"Who are the top 3 agents by FCR?"*
            """)

    # Show existing messages
    for msg in st.session_state.cc_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("tools_used"):
                tools_str = " → ".join(msg["tools_used"])
                st.caption(f"🔧 Tools: {tools_str}")
            if msg.get("response_time"):
                st.caption(
                    f"⏱️ {msg['response_time']:.1f}s"
                )

    # Handle sidebar button clicks
    sidebar_q = st.session_state.pop("sidebar_q", None)
    prompt = st.chat_input(
        "Ask about performance, KPIs, trends..."
    ) or sidebar_q

    # Process input
    if prompt:
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.cc_messages.append({
            "role": "user",
            "content": prompt
        })

        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner(
                "Analyzing call center data..."
            ):
                start = time.time()
                try:
                    from utils import run_agent
                    result = run_agent(
                        question=prompt,
                        session_id="streamlit",
                        llm=llm,
                        vectorstore=vs
                    )
                    elapsed = time.time() - start

                    answer = result["answer"]
                    tools = result.get("tools_used", [])

                    # Display answer
                    st.markdown(answer)

                    # Show metadata
                    meta_col1, meta_col2 = st.columns(2)
                    with meta_col1:
                        if tools:
                            st.caption(
                                f"🔧 Tools: "
                                f"{' → '.join(tools)}"
                            )
                    with meta_col2:
                        st.caption(f"⏱️ {elapsed:.1f}s")

                    # Save to history
                    st.session_state.cc_messages.append({
                        "role":          "assistant",
                        "content":       answer,
                        "tools_used":    tools,
                        "response_time": elapsed
                    })

                except Exception as e:
                    err = str(e)
                    st.error(f"Error: {err}")

                    if "rate" in err.lower():
                        st.warning(
                            "⏳ Groq rate limit hit. "
                            "Wait 30 seconds and try again."
                        )
                    elif "vectorstore" in err.lower():
                        st.warning(
                            "Vector store not found. "
                            "Run: python setup_data.py first"
                        )
                    else:
                        st.info(
                            "Try refreshing the page. "
                            "If error continues paste it "
                            "in the terminal for debugging."
                        )
