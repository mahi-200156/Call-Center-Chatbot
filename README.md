#  Call Center AI Analyst

> An AI agent that answers natural language
> questions about call center KPI performance — built by a
> Data Analyst who works with this data every day.

#  Live Demo
 [**Try the app here**](https://call-center-chatbot.streamlit.app/)

# The Problem This Solves

Call center managers currently:
- Open Power BI dashboards manually
- Run multiple reports to identify issues
- Spend hours correlating data across agents and teams
- Need analyst support for every ad-hoc question
  
A manager who wants to know why an agent is underperforming must open dashboards, run queries, and cross-reference data manually.

**This system replaces that workflow — type a question, get a structured analysis in seconds.**

Manager types: "Why is Vikram underperforming?"

System responds in seconds:
"Vikram Nair's AHT of 6.2 min is 38% above team average.
 FCR has declined from 71% in Q1 to 65% in Q4 — a worsening trend.
 CSAT at 74% is 11 pts below target.
 Recommend immediate coaching on talk time management."

##  Why This Is An AGENT, Not Just RAG

Most AI chatbots just retrieve documents and answer.
This system **which tools to call** based on your question.

| Question Type | Tool Agent Chooses |
| "What is FCR?" | `search_knowledge_base` (RAG) |
| "Show Ravi's AHT" | `get_agent_metrics` (SQL) |
| "Team A vs Team B" | `get_team_comparison` (SQL) |
| "Who has worst CSAT?" | `get_top_bottom_agents` (SQL) |
| "Did FCR improve Q1→Q4?" | `calculate_metric_change` (SQL+Math) |
| "Why is this agent underperforming?" | **3 tools combined** |

The LLM reasons about which tools to call — this is the ReAct (Reason + Act) pattern.

The `tools_used` field in every response shows exactly which tools were called — full transparency.


# Architecture

```
User Question
      │
      ▼
Streamlit UI
      │
      ▼
FastAPI /chat endpoint
      │
      ▼
ReAct Agent (Groq Llama 3.3 70B)
"Which tool do I need?"
      │
  ┌───┴──────────────────────────────────────┐
  │                                            │
  ▼                                            ▼
SQL Tools                               RAG Tool
  get_agent_metrics()                   search_knowledge_base()
  get_team_comparison()                 FAISS Vector Store
  get_top_bottom_agents()               (monthly summaries +
  calculate_metric_change()              agent profiles +
                                         KPI definitions)
  │                                            │
  └───────────────┬───────────────────────────┘
                  ▼
         Agent synthesizes results
         Generates final analysis
                  │
                  ▼
         Response: answer + sources + tools_used


# RAGAS Evaluation Results

The RAG pipeline is validated using the [RAGAS framework](https://github.com/explodinggradients/ragas).

| Metric | Score | Meaning |
|---|---|---|
| **Faithfulness** | **1.000** ✅ | Zero hallucination — answers grounded in documents |
| **Answer Relevancy** | **0.961** ✅ | Answers directly address questions |
| **Context Precision** | **0.667** ⚠️ | Retrieval has room for improvement |
| **Overall** | **0.876** ✅ | Pipeline is reliable for production |

> Tested on 10 call center domain questions.
> Run evaluation: `python evaluate.py`


# Features

**5 Agent Tools:**
- `search_knowledge_base` — Semantic search on KPI docs and summaries
- `get_agent_metrics` — Real-time SQL query for any agent's KPIs
- `get_team_comparison` — Team A vs Team B aggregate comparison
- `get_top_bottom_agents` — Rankings and leaderboards by any KPI
- `calculate_metric_change` — Percentage change between any two periods

**Multi-turn Memory:**
- Conversation history per session using Python deque
- Follow-up questions reference previous answers
- Clear history endpoint to reset context

**Domain-Aware Logic:**
- KPI direction built into tools (AHT lower = better, FCR higher = better)
- Sort direction flips automatically based on metric type
- Target values baked into system prompt

# Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| API | FastAPI |
| Agent Pattern | ReAct (LangChain) |
| LLM | Groq Llama 3.3 70B (Free) |
| Embeddings | HuggingFace all-MiniLM-L6-v2 (Local) |
| Vector Store | FAISS |
| Database | SQLite |
| Evaluation | RAGAS |

**Total API Cost: $0**


#Data

**10 Agents:**
- Team A (Mumbai): Ravi Sharma, Pooja Mehta, Vikram Nair, Rahul Joshi, Amit Gupta
- Team B (Bangalore): Arjun Kumar, Sneha Iyer, Divya Patel, Kavya Menon, Priya Reddy

**12 Months:** January 2024 — December 2024
**5 KPIs per agent per month:**

| KPI | Target | Direction |
| AHT (Average Handle Time) | < 5.0 min | Lower is better |
| FCR (First Call Resolution) | > 80% | Higher is better |
| CSAT (Customer Satisfaction) | > 85% | Higher is better |
| Adherence (Schedule) | > 90% | Higher is better |
| Calls Handled | — | Volume metric |


# Domain Expertise

This project was built by a Data Analyst with 2 years of hands-on experience working with real call center KPI data across enterprise clients.

The domain knowledge is embedded in tool logic:
- AHT direction (lower = better) → rankings sort ascending
- FCR/CSAT/Adherence (higher = better) → sort descending
- KPI targets are real industry benchmarks
- Analysis language matches operational reporting

#Run Locally

# 1. Clone
git clone https://github.com/maahii6/cc-ai-analyst
cd cc-ai-analyst

# 2. Install
pip install -r requirements.txt

# 3. Add API key
echo "GROQ_API_KEY=your_key_here" > .env

# 4. Database and vector store included
#    Run setup only if they're missing:
python setup_data.py

# 5. Start Streamlit
streamlit run streamlit_app.py

# 6. Run RAGAS evaluation
python evaluate.py

# Project Structure

cc-ai-analyst/
├── main.py                  # FastAPI endpoints
├── utils.py                 # 5 agent tools + runner
├── setup_data.py            # DB + vector store creation
├── schemas.py               # Pydantic models
├── evaluate.py              # RAGAS evaluation
├── streamlit_app.py         # Streamlit UI
├── requirements.txt
├── cc_database.db           # SQLite (600+ data points)
├── vectorstore_cc/          # FAISS index
├── evaluation_results.json  # RAGAS detailed results
├── evaluation_summary.txt   # RAGAS summary
└── screenshots/             # Demo screenshots

#Example Questions

Performance:
"Why is Vikram Nair underperforming?"
"Show Kavya Menon full 2024 performance"
"Which agents are below FCR target?"

Comparisons:
"Compare Team A vs Team B for full year"
"Which team has better adherence in Q3?"

Rankings:
"Who are top 3 agents by CSAT?"
"Which agents need coaching most urgently?"

Trends:
"How did FCR change from Q1 to Q4?"
"Which KPI declined most in Q4?"

Definitions:
"What is AHT and why does it matter?"
"What are the KPI targets?"
