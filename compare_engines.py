"""
compare_engines.py
------------------
Compares the ORIGINAL ReAct agent with the LangGraph agent on the same
questions, using the same LLM and vector store.

What it measures (all computed from real runs, nothing is made up):
  - Success rate     : did the agent return an answer without an error?
  - Right-tool rate  : did it call the tool we expected for that question?
  - Average time     : seconds per question
  - Average tools    : tool calls per question

What it does NOT measure:
  - Whether the numbers in each answer are correct. Open
    engine_comparison.md and check the answers yourself (there is a
    blank "Correct?" column for that).

How to run (from the CallCenter folder, venv on):
    python compare_engines.py

Output:
    engine_comparison.json   (all raw results)
    engine_comparison.md     (table + answers side by side, for your README)

Free Groq limits are small, so the script waits between questions.
"""

import json
import os
import time
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

from utils import init_embeddings, init_llm, load_vectorstore, run_agent  # noqa: E402

PAUSE_SECONDS = int(os.getenv("COMPARE_PAUSE", "15"))       # wait between runs
RATE_LIMIT_WAIT = int(os.getenv("COMPARE_RATE_WAIT", "65"))  # wait after a 429

# expected_any = the answer should use AT LEAST ONE of these tools
TEST_QUESTIONS = [
    {"question": "What is AHT and what is its target?",
     "expected_any": ["search_knowledge_base"]},
    {"question": "Who has the worst FCR in Q3?",
     "expected_any": ["get_top_bottom_agents"]},
    {"question": "Compare Team A vs Team B for the full year",
     "expected_any": ["get_team_comparison"]},
    {"question": "Show Kavya Menon complete performance",
     "expected_any": ["get_agent_metrics"]},
    {"question": "How did FCR change from Q1 to Q4?",
     "expected_any": ["calculate_metric_change"]},
    {"question": "How did Team B FCR change from Q1 to Q4?",
     "expected_any": ["calculate_metric_change"]},
    {"question": "Which agents are below CSAT target?",
     "expected_any": ["get_top_bottom_agents", "get_agent_metrics"]},
    {"question": "Why is Vikram Nair underperforming?",
     "expected_any": ["get_agent_metrics"]},
]

ENGINES = ["react", "langgraph"]


def _looks_rate_limited(text: str) -> bool:
    t = text.lower()
    return "429" in t or "rate limit" in t or "rate_limit" in t


def _looks_failed(answer: str, error) -> bool:
    if error:
        return True
    a = answer.strip().lower()
    return (
        not a
        or a.startswith("sorry")
        or "iteration limit" in a
        or "time limit" in a
    )


def ask(engine: str, question: str, session_id: str, llm, vs) -> dict:
    """Run one question on one engine. Waits and retries once on a rate limit."""
    os.environ["AGENT_ENGINE"] = engine
    for attempt in range(2):
        start = time.time()
        error = None
        try:
            r = run_agent(
                question=question, session_id=session_id, llm=llm, vectorstore=vs
            )
        except Exception as e:  # the old agent raises on errors
            r = {"answer": "", "tools_used": []}
            error = str(e)[:300]
        elapsed = time.time() - start

        text = error or r.get("answer", "")
        if attempt == 0 and _looks_rate_limited(text):
            print(f"      rate limit hit, waiting {RATE_LIMIT_WAIT}s and retrying once...")
            time.sleep(RATE_LIMIT_WAIT)
            continue
        break

    return {
        "engine": engine,
        "answer": r.get("answer", ""),
        "tools_used": r.get("tools_used", []),
        "seconds": round(elapsed, 2),
        "error": error,
        "failed": _looks_failed(r.get("answer", ""), error),
    }


def summarize(rows: list) -> dict:
    summary = {}
    for engine in ENGINES:
        mine = [r for r in rows if r["engine"] == engine]
        n = len(mine)
        ok = [r for r in mine if not r["failed"]]
        right = [r for r in mine if r["tool_ok"]]
        summary[engine] = {
            "questions": n,
            "success_rate": round(len(ok) / n, 3) if n else 0,
            "right_tool_rate": round(len(right) / n, 3) if n else 0,
            "avg_seconds": round(sum(r["seconds"] for r in mine) / n, 2) if n else 0,
            "avg_tool_calls": round(sum(len(r["tools_used"]) for r in mine) / n, 2) if n else 0,
        }
    return summary


def main():
    print("\nLoading models...")
    llm = init_llm()
    vs = load_vectorstore(init_embeddings())
    print(f"LLM: {getattr(llm, 'model_name', 'unknown')}")
    print(f"{len(TEST_QUESTIONS)} questions x {len(ENGINES)} engines "
          f"(about {len(TEST_QUESTIONS) * len(ENGINES) * (PAUSE_SECONDS + 10) // 60} min)\n")

    rows = []
    for i, case in enumerate(TEST_QUESTIONS):
        q = case["question"]
        print(f"[{i + 1}/{len(TEST_QUESTIONS)}] {q}")
        # alternate which engine goes first so neither one always gets the "first" slot
        order = ENGINES if i % 2 == 0 else list(reversed(ENGINES))
        for engine in order:
            res = ask(engine, q, f"cmp-{engine}-{i}", llm, vs)
            res["question"] = q
            res["expected_any"] = case["expected_any"]
            res["tool_ok"] = bool(set(res["tools_used"]) & set(case["expected_any"]))
            rows.append(res)
            flag = "FAILED" if res["failed"] else "ok"
            print(f"   {engine:<9} {flag:<6} {res['seconds']:>5.1f}s  tools={res['tools_used']}")
            time.sleep(PAUSE_SECONDS)

    summary = summarize(rows)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model = getattr(llm, "model_name", "unknown")

    with open("engine_comparison.json", "w", encoding="utf-8") as f:
        json.dump({"timestamp": timestamp, "model": model,
                   "summary": summary, "rows": rows}, f, indent=2)

    lines = [
        "# ReAct vs LangGraph comparison", "",
        f"Run at {timestamp} | model: `{model}` | {len(TEST_QUESTIONS)} questions", "",
        "| Metric | ReAct | LangGraph |", "|---|---|---|",
        f"| Success rate | {summary['react']['success_rate']:.0%} | {summary['langgraph']['success_rate']:.0%} |",
        f"| Right tool used | {summary['react']['right_tool_rate']:.0%} | {summary['langgraph']['right_tool_rate']:.0%} |",
        f"| Avg seconds per question | {summary['react']['avg_seconds']} | {summary['langgraph']['avg_seconds']} |",
        f"| Avg tool calls per question | {summary['react']['avg_tool_calls']} | {summary['langgraph']['avg_tool_calls']} |",
        "", "## Answers to check by hand", "",
    ]
    for case in TEST_QUESTIONS:
        q = case["question"]
        lines += [f"### {q}", "", "| Engine | Tools used | Seconds | Correct? (fill in) |", "|---|---|---|---|"]
        for r in [x for x in rows if x["question"] == q]:
            lines.append(f"| {r['engine']} | {', '.join(r['tools_used']) or '-'} | {r['seconds']} | |")
        lines.append("")
        for r in [x for x in rows if x["question"] == q]:
            ans = (r["error"] or r["answer"]).strip().replace("\n", "\n> ")
            lines += [f"**{r['engine']} answer:**", "", f"> {ans}", ""]
    with open("engine_comparison.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("\n" + "=" * 60)
    for engine in ENGINES:
        s = summary[engine]
        print(f"{engine:<10} success {s['success_rate']:.0%} | right tool {s['right_tool_rate']:.0%} "
              f"| {s['avg_seconds']}s avg | {s['avg_tool_calls']} tool calls avg")
    print("=" * 60)
    print("Saved: engine_comparison.json, engine_comparison.md")
    print("Now open engine_comparison.md and check the answers by hand.\n")


if __name__ == "__main__":
    main()
