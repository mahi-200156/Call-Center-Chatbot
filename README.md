#  Call Center AI Analyst

> An AI-powered analytics agent that answers natural language
> questions about call center KPI performance — built by a
> Data Analyst who works with this data every day.

## The Problem This Solves

Call center managers currently:
- Open Power BI dashboards manually
- Run multiple reports to identify issues
- Spend hours correlating data across agents and teams
- Need analyst support for every ad-hoc question

**This system replaces that workflow:**

```
Manager types: "Why is Vikram underperforming?"

System responds in seconds:
"Vikram Nair's AHT of 6.2 min is 38% above team
average. FCR has declined from 71% in Q1 to 65%
in Q4 — a worsening trend. CSAT at 74% is 11 pts
below target. Recommend immediate coaching on
talk time management."
```

##  Why This Is An AGENT, Not Just RAG

Most AI chatbots just retrieve documents and answer.
This system **decides what to do** based on your question.

| Question Type | Tool Agent Chooses |
| "What is FCR?" | `search_knowledge_base` (RAG) |
| "Show Ravi's AHT" | `get_agent_metrics` (SQL) |
| "Team A vs Team B" | `get_team_comparison` (SQL) |
| "Who has worst CSAT?" | `get_top_bottom_agents` (SQL) |
| "Did FCR improve Q1→Q4?" | `calculate_metric_change` (SQL+Math) |
| "Why is this agent poor?" | **3 tools combined** |

The LLM reasons about which tools to call —
this is the ReAct (Reason + Act) pattern.

## Architecture

```
User Question
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

##  Features

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

## Project Structure

cc_chatbot/
├── main.py           # FastAPI app + 4 endpoints
├── utils.py          # 5 agent tools + ReAct agent runner
├── setup_data.py     # One-time: creates DB + vector store
├── schemas.py        # Pydantic request/response models
├── requirements.txt  # All dependencies
├── .env              # GROQ_API_KEY (not committed)
├── cc_database.db    # SQLite (created by setup)
├── vectorstore_cc/   # FAISS index (created by setup)
└── screenshots/      # Demo screenshots for README


##  Data

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


## Domain Expertise

This project was built by a Data Analyst with 2 years
of hands-on experience working with real call center
KPI data across enterprise clients.

The domain knowledge is embedded in the system:
- Tool logic knows AHT lower = better (sort ascending for rankings)
- Tool logic knows FCR higher = better (sort descending)
- KPI targets are real industry benchmarks
- Analysis language matches what operations managers use
