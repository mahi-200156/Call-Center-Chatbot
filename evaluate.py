"""
evaluate.py — RAGAS Evaluation for Call Center AI Analyst
══════════════════════════════════════════════════════════

What this does:
  Tests the RAG pipeline (search_knowledge_base tool)
  on 10 call center questions and measures:
    → Faithfulness:      Is answer grounded in docs? (no hallucination)
    → Answer Relevancy:  Does answer address the question?
    → Context Precision: Are retrieved chunks actually useful?

How to run:
  python evaluate.py

Output:
  → Scores printed to terminal
  → Results saved to evaluation_results.json
  → Summary saved to evaluation_summary.txt

Note:
  SQL tools (get_agent_metrics, get_team_comparison etc.)
  are not RAG — they query SQL directly, so RAGAS
  does not apply to them. Only search_knowledge_base
  uses RAG retrieval and is evaluated here.
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

load_dotenv()


# ─────────────────────────────────────────────────────────────────
# TEST DATASET
# 10 questions covering all 3 document types in the vector store:
#   → KPI definitions (4 docs)
#   → Monthly team summaries (24 docs)
#   → Agent annual profiles (10 docs)
# ─────────────────────────────────────────────────────────────────

TEST_CASES = [

    # ── KPI Definitions ────────────────────────────────────────────
    {
        "question": "What is AHT and what is the target for it?",
        "ground_truth": (
            "AHT stands for Average Handle Time. It measures the average "
            "time an agent spends on a call including talk time, hold time, "
            "and after-call work. The target is below 5.0 minutes. Lower "
            "AHT is better as it indicates efficient call handling."
        )
    },
    {
        "question": "What does FCR mean and why does it matter?",
        "ground_truth": (
            "FCR stands for First Call Resolution. It measures the percentage "
            "of customer calls resolved in a single interaction without "
            "requiring callback or follow-up. The target is above 80%. "
            "Higher FCR indicates better customer experience and fewer "
            "repeat calls."
        )
    },
    {
        "question": "What is CSAT and what is its target?",
        "ground_truth": (
            "CSAT stands for Customer Satisfaction Score measured through "
            "post-call surveys. The target is above 85%. Higher CSAT "
            "indicates better customer experience during the interaction. "
            "Low CSAT is often linked to unresolved issues or poor agent attitude."
        )
    },
    {
        "question": "What is Schedule Adherence and what is the target?",
        "ground_truth": (
            "Schedule Adherence measures the percentage of time agents "
            "follow their scheduled shifts — login time, break compliance, "
            "and logout time. The target is above 90%. Low adherence "
            "directly impacts service levels and call center staffing."
        )
    },
    {
        "question": "What are the common causes of high AHT?",
        "ground_truth": (
            "Common causes of high AHT include poor product knowledge, "
            "long hold times, system slowness, and complex customer issues. "
            "High AHT indicates the agent may need more training or has "
            "inefficient call handling practices."
        )
    },
    {
        "question": "What causes low FCR in a call center?",
        "ground_truth": (
            "Common causes of low FCR include insufficient agent training, "
            "lack of tools or system access, complex issues requiring "
            "escalation, and incorrect resolution. Low FCR means customers "
            "are calling back repeatedly without having their issues resolved."
        )
    },

    # ── Agent Profiles ──────────────────────────────────────────────
    {
        "question": "Who are the agents in Team A and where are they located?",
        "ground_truth": (
            "Team A is based in Mumbai and includes Ravi Sharma, Pooja Mehta, "
            "Vikram Nair, Rahul Joshi, and Amit Gupta. "
            "Their team lead is Vandana Singh."
        )
    },
    {
        "question": "Who are the agents in Team B?",
        "ground_truth": (
            "Team B is based in Bangalore and includes Arjun Kumar, "
            "Sneha Iyer, Divya Patel, Kavya Menon, and Priya Reddy. "
            "Their team lead is Rahul Verma."
        )
    },

    # ── KPI Overview ───────────────────────────────────────────────
    {
        "question": "What KPI targets should call center agents meet?",
        "ground_truth": (
            "Agents should meet four KPI targets: AHT below 5.0 minutes, "
            "FCR above 80%, CSAT above 85%, and Schedule Adherence "
            "above 90%."
        )
    },
    {
        "question": "Which KPIs are tracked for each agent monthly?",
        "ground_truth": (
            "Five KPIs are tracked for each agent every month: "
            "AHT (Average Handle Time), FCR (First Call Resolution), "
            "CSAT (Customer Satisfaction Score), Schedule Adherence, "
            "and Calls Handled count."
        )
    },
]


# ─────────────────────────────────────────────────────────────────
# RAG PIPELINE
# Runs search_knowledge_base + LLM generation for each question
# ─────────────────────────────────────────────────────────────────

def run_rag_for_question(
    question: str,
    vectorstore: FAISS,
    llm: ChatGroq
) -> dict:
    """
    Runs the RAG component for a single question.
    Returns the answer and retrieved context chunks.

    This mirrors exactly what search_knowledge_base tool does
    in the main agent pipeline.
    """

    # Step 1: Retrieve top 3 relevant documents from FAISS
    docs = vectorstore.similarity_search(question, k=2)
    contexts = [doc.page_content for doc in docs]

    # Step 2: Generate answer using LLM with retrieved context
    context_text = "\n\n---\n\n".join(contexts)

    messages = [
        SystemMessage(content=(
            "You are a Call Center Analytics assistant. "
            "Answer the question using ONLY the provided context. "
            "If the answer is not in the context, say exactly: "
            "'I don't have that information in the knowledge base.' "
            "Be concise and accurate. Do not add information not in the context."
        )),
        HumanMessage(content=(
            f"Context:\n{context_text}\n\n"
            f"Question: {question}"
        ))
    ]

    response = llm.invoke(messages)

    return {
        "answer":   response.content,
        "contexts": contexts
    }


# ─────────────────────────────────────────────────────────────────
# MAIN EVALUATION
# ─────────────────────────────────────────────────────────────────

def run_evaluation():

    print("\n" + "="*60)
    print("   CALL CENTER AI ANALYST — RAGAS EVALUATION")
    print("="*60)
    print(f"   Running {len(TEST_CASES)} test cases...")
    print(f"   Metrics: Faithfulness, Answer Relevancy, Context Precision")
    print("="*60 + "\n")

    # ── Initialize models ──────────────────────────────────────────
    print("Loading models...")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )
    print("  ✅ Groq LLM loaded")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    print("  ✅ HuggingFace embeddings loaded")

    vectorstore = FAISS.load_local(
        "vectorstore_cc",
        embeddings,
        allow_dangerous_deserialization=True
    )
    print("  ✅ FAISS vector store loaded")
    print()

    # ── Run RAG pipeline for each test case ───────────────────────
    print("Running RAG pipeline on test questions...")
    print("-" * 60)

    questions  = []
    answers    = []
    contexts   = []
    ground_truths = []

    for i, case in enumerate(TEST_CASES, 1):
        q = case["question"]
        gt = case["ground_truth"]

        print(f"  [{i:02d}/{len(TEST_CASES)}] {q[:55]}...")

        result = run_rag_for_question(q, vectorstore, llm)

        questions.append(q)
        answers.append(result["answer"])
        contexts.append(result["contexts"])
        ground_truths.append(gt)

    print("-" * 60)
    print(f"  ✅ All {len(TEST_CASES)} questions processed\n")

    # ── Build RAGAS dataset ───────────────────────────────────────
    dataset = Dataset.from_dict({
        "question":     questions,
        "answer":       answers,
        "contexts":     contexts,
        "ground_truth": ground_truths
    })

    # ── Configure RAGAS to use Groq + HuggingFace ─────────────────
    # (instead of default OpenAI)
    ragas_llm = LangchainLLMWrapper(ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    ))

    ragas_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )
    )

    # ── Run RAGAS evaluation ──────────────────────────────────────
    print("Running RAGAS evaluation (this takes 2-5 minutes)...")
    print("Each metric calls the LLM to judge quality.\n")
    
    
    import time
    # Add a small delay between test cases
    # to avoid hitting Groq rate limits
    print("Adding delay to avoid rate limits...")
    time.sleep(2)

    results = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
        ],
        llm=ragas_llm,
        embeddings=ragas_embeddings
    )

    # ── Extract scores ─────────────────────────────────────────────
    scores_df = results.to_pandas()

    faithfulness_score     = round(scores_df["faithfulness"].mean(), 3)
    answer_relevancy_score = round(scores_df["answer_relevancy"].mean(), 3)
    context_precision_score = round(scores_df["context_precision"].mean(), 3)
    overall_score          = round(
        (faithfulness_score + answer_relevancy_score + context_precision_score) / 3,
        3
    )

    # ── Print results ──────────────────────────────────────────────
    print("\n" + "="*60)
    print("   EVALUATION RESULTS")
    print("="*60)
    print(f"""
  Faithfulness:       {faithfulness_score:.3f}  {'✅ GOOD' if faithfulness_score >= 0.75 else '⚠️  NEEDS IMPROVEMENT'}
  (Is answer grounded in retrieved docs?)

  Answer Relevancy:   {answer_relevancy_score:.3f}  {'✅ GOOD' if answer_relevancy_score >= 0.75 else '⚠️  NEEDS IMPROVEMENT'}
  (Does answer address the question?)

  Context Precision:  {context_precision_score:.3f}  {'✅ GOOD' if context_precision_score >= 0.70 else '⚠️  NEEDS IMPROVEMENT'}
  (Are retrieved chunks actually useful?)

  ──────────────────────────────────────
  Overall Score:      {overall_score:.3f}  {'✅ PIPELINE IS RELIABLE' if overall_score >= 0.75 else '⚠️  NEEDS TUNING'}
    """)

    print("Score Guide:")
    print("  0.0 - 0.5  → Poor     (hallucinating or irrelevant)")
    print("  0.5 - 0.7  → Moderate (needs improvement)")
    print("  0.7 - 0.85 → Good     (reliable for production)")
    print("  0.85 - 1.0 → Excellent (well-tuned pipeline)")
    print("="*60 + "\n")

    # ── Per-question breakdown ─────────────────────────────────────
    print("Per-Question Breakdown:")
    print("-"*60)
    for i, row in scores_df.iterrows():
        q_short = TEST_CASES[i]["question"][:50] + "..."
        f_score  = round(row["faithfulness"], 2)
        ar_score = round(row["answer_relevancy"], 2)
        cp_score = round(row["context_precision"], 2)
        flag = "✅" if min(f_score, ar_score, cp_score) >= 0.7 else "⚠️"
        print(
            f"  {flag} Q{i+1:02d} | "
            f"Faith:{f_score:.2f} "
            f"Rel:{ar_score:.2f} "
            f"Prec:{cp_score:.2f} | "
            f"{q_short}"
        )

    # ── Save results ───────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save detailed JSON
    full_results = {
        "timestamp":   timestamp,
        "num_tests":   len(TEST_CASES),
        "metrics": {
            "faithfulness":      faithfulness_score,
            "answer_relevancy":  answer_relevancy_score,
            "context_precision": context_precision_score,
            "overall":           overall_score
        },
        "per_question": [
            {
                "question":          TEST_CASES[i]["question"],
                "faithfulness":      round(scores_df["faithfulness"][i], 3),
                "answer_relevancy":  round(scores_df["answer_relevancy"][i], 3),
                "context_precision": round(scores_df["context_precision"][i], 3),
                "answer":            answers[i]
            }
            for i in range(len(TEST_CASES))
        ]
    }

    with open("evaluation_results.json", "w") as f:
        json.dump(full_results, f, indent=2)

    # Save readable summary
    with open("evaluation_summary.txt", "w") as f:
        f.write(f"Call Center AI Analyst — RAGAS Evaluation\n")
        f.write(f"Run at: {timestamp}\n")
        f.write(f"Test cases: {len(TEST_CASES)}\n\n")
        f.write(f"Faithfulness:       {faithfulness_score:.3f}\n")
        f.write(f"Answer Relevancy:   {answer_relevancy_score:.3f}\n")
        f.write(f"Context Precision:  {context_precision_score:.3f}\n")
        f.write(f"Overall:            {overall_score:.3f}\n")

    print("\n  💾 Results saved:")
    print("     evaluation_results.json  (detailed per-question)")
    print("     evaluation_summary.txt   (summary for README)\n")
    print("="*60 + "\n")

    return full_results


# ─────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_evaluation()