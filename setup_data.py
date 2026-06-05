import sqlite3
import random
from datetime import datetime
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document

random.seed(42)

AGENTS = [
    {"agent_id": "AGT001", "name": "Ravi Sharma",  "team": "Team A", "team_lead": "Vandana Singh", "location": "Mumbai",    "band": "B2"},
    {"agent_id": "AGT002", "name": "Pooja Mehta",  "team": "Team A", "team_lead": "Vandana Singh", "location": "Mumbai",    "band": "B2"},
    {"agent_id": "AGT003", "name": "Arjun Kumar",  "team": "Team B", "team_lead": "Rahul Verma",   "location": "Bangalore", "band": "B3"},
    {"agent_id": "AGT004", "name": "Sneha Iyer",   "team": "Team B", "team_lead": "Rahul Verma",   "location": "Bangalore", "band": "B2"},
    {"agent_id": "AGT005", "name": "Vikram Nair",  "team": "Team A", "team_lead": "Vandana Singh", "location": "Mumbai",    "band": "B3"},
    {"agent_id": "AGT006", "name": "Divya Patel",  "team": "Team B", "team_lead": "Rahul Verma",   "location": "Bangalore", "band": "B2"},
    {"agent_id": "AGT007", "name": "Rahul Joshi",  "team": "Team A", "team_lead": "Vandana Singh", "location": "Mumbai",    "band": "B2"},
    {"agent_id": "AGT008", "name": "Kavya Menon",  "team": "Team B", "team_lead": "Rahul Verma",   "location": "Bangalore", "band": "B3"},
    {"agent_id": "AGT009", "name": "Amit Gupta",   "team": "Team A", "team_lead": "Vandana Singh", "location": "Mumbai",    "band": "B2"},
    {"agent_id": "AGT010", "name": "Priya Reddy",  "team": "Team B", "team_lead": "Rahul Verma",   "location": "Bangalore", "band": "B2"},
]

MONTHS = ["Jan-2024","Feb-2024","Mar-2024","Apr-2024","May-2024","Jun-2024",
          "Jul-2024","Aug-2024","Sep-2024","Oct-2024","Nov-2024","Dec-2024"]

AGENT_PROFILES = {
    "AGT001": (4.2, 84, 88, 93),
    "AGT002": (5.8, 71, 78, 82),
    "AGT003": (3.9, 89, 92, 95),
    "AGT004": (4.5, 80, 85, 90),
    "AGT005": (6.2, 68, 74, 79),
    "AGT006": (4.1, 86, 90, 94),
    "AGT007": (5.1, 76, 82, 87),
    "AGT008": (3.8, 91, 93, 96),
    "AGT009": (4.7, 79, 83, 89),
    "AGT010": (5.5, 73, 80, 85),
}

def gen(base, var, i, trend=0):
    v = base + random.uniform(-var, var) + (trend * i) + (0.3 if i >= 9 else 0)
    return round(v, 2)


def create_database():
    print("Creating database...")
    conn = sqlite3.connect("cc_database.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS agents
        (agent_id TEXT PRIMARY KEY, name TEXT, team TEXT,
         team_lead TEXT, location TEXT, band TEXT)""")

    c.execute("""CREATE TABLE IF NOT EXISTS performance
        (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT, agent_name TEXT,
         month_year TEXT, team TEXT, location TEXT,
         aht REAL, fcr REAL, csat REAL, adherence REAL, calls_handled INTEGER)""")

    c.execute("""CREATE TABLE IF NOT EXISTS kpi_targets
        (metric TEXT PRIMARY KEY, target REAL, unit TEXT, good_direction TEXT)""")

    for a in AGENTS:
        c.execute("INSERT OR REPLACE INTO agents VALUES (?,?,?,?,?,?)",
                  (a["agent_id"],a["name"],a["team"],a["team_lead"],a["location"],a["band"]))

    for t in [("AHT",5.0,"minutes","DECREASE"),("FCR",80.0,"%","INCREASE"),
              ("CSAT",85.0,"%","INCREASE"),("Adherence",90.0,"%","INCREASE")]:
        c.execute("INSERT OR REPLACE INTO kpi_targets VALUES (?,?,?,?)", t)

    for a in AGENTS:
        ba, bf, bc, bad = AGENT_PROFILES[a["agent_id"]]
        for i, m in enumerate(MONTHS):
            aht = max(2.5, min(9.0, gen(ba, 0.4, i, 0.02)))
            fcr = max(50, min(100, gen(bf, 3.0, i, -0.1)))
            csat= max(50, min(100, gen(bc, 2.5, i, -0.08)))
            adh = max(60, min(100, gen(bad,3.0, i, -0.05)))
            calls = random.randint(180, 260)
            c.execute("""INSERT INTO performance
                (agent_id,agent_name,month_year,team,location,aht,fcr,csat,adherence,calls_handled)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (a["agent_id"],a["name"],m,a["team"],a["location"],
                 round(aht,2),round(fcr,1),round(csat,1),round(adh,1),calls))

    conn.commit()
    conn.close()
    print(f"Database ready: {len(AGENTS)} agents × {len(MONTHS)} months")


def build_vectorstore():
    print("Building vector store...")
    print("  Loading HuggingFace model")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    conn = sqlite3.connect("cc_database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    docs = []

    # Monthly team summaries
    for month in MONTHS:
        for team in ["Team A", "Team B"]:
            rows = cursor.execute("""
                SELECT agent_name,aht,fcr,csat,adherence,calls_handled
                FROM performance WHERE month_year=? AND team=?
            """, (month, team)).fetchall()
            if not rows: continue

            avg_aht  = round(sum(r["aht"]  for r in rows)/len(rows), 2)
            avg_fcr  = round(sum(r["fcr"]  for r in rows)/len(rows), 1)
            avg_csat = round(sum(r["csat"] for r in rows)/len(rows), 1)
            avg_adh  = round(sum(r["adherence"] for r in rows)/len(rows), 1)

            details = "\n".join([
                f"  - {r['agent_name']}: AHT={r['aht']}min, FCR={r['fcr']}%, CSAT={r['csat']}%, Adherence={r['adherence']}%"
                for r in rows
            ])

            docs.append(Document(
                page_content=f"""Monthly Report — {team} — {month}
Averages: AHT={avg_aht}min | FCR={avg_fcr}% | CSAT={avg_csat}% | Adherence={avg_adh}%
Targets:  AHT<5.0 | FCR>80% | CSAT>85% | Adherence>90%
Agents:
{details}
Total calls: {sum(r['calls_handled'] for r in rows)}""",
                metadata={"type": "monthly_summary", "month": month, "team": team}
            ))

    # Agent annual profiles
    for a in AGENTS:
        rows = cursor.execute("""
            SELECT month_year,aht,fcr,csat,adherence,calls_handled
            FROM performance WHERE agent_id=? ORDER BY rowid
        """, (a["agent_id"],)).fetchall()

        avg_aht  = round(sum(r["aht"]  for r in rows)/len(rows), 2)
        avg_fcr  = round(sum(r["fcr"]  for r in rows)/len(rows), 1)
        avg_csat = round(sum(r["csat"] for r in rows)/len(rows), 1)
        avg_adh  = round(sum(r["adherence"] for r in rows)/len(rows), 1)

        trend = "\n".join([
            f"  {r['month_year']}: AHT={r['aht']}min FCR={r['fcr']}% CSAT={r['csat']}% Adh={r['adherence']}%"
            for r in rows
        ])

        docs.append(Document(
            page_content=f"""Agent Profile — {a['name']} ({a['agent_id']})
Team: {a['team']} | Lead: {a['team_lead']} | Location: {a['location']} | Band: {a['band']}
2024 Averages: AHT={avg_aht}min | FCR={avg_fcr}% | CSAT={avg_csat}% | Adherence={avg_adh}%
Monthly Trend:
{trend}""",
            metadata={"type": "agent_profile", "agent_id": a["agent_id"],
                      "agent_name": a["name"], "team": a["team"]}
        ))

    # KPI definitions
    kpi_defs = {
        "AHT": "Average Handle Time — average minutes per call including talk, hold and wrap-up. Target <5.0 min. High AHT indicates inefficiency or complex queries.",
        "FCR": "First Call Resolution — % of calls resolved without callback. Target >80%. Low FCR means customers call back repeatedly.",
        "CSAT": "Customer Satisfaction Score — post-call survey rating. Target >85%. Low CSAT indicates poor customer experience.",
        "Adherence": "Schedule Adherence — % of time agents follow their scheduled shifts. Target >90%. Low adherence impacts service levels."
    }
    for kpi, defn in kpi_defs.items():
        docs.append(Document(
            page_content=f"KPI Definition — {kpi}\n{defn}",
            metadata={"type": "kpi_definition", "kpi": kpi}
        ))

    conn.close()
    vs = FAISS.from_documents(docs, embeddings)
    vs.save_local("vectorstore_cc")
    print(f"Vector store saved: {len(docs)} documents")


if __name__ == "__main__":
    print("\n Setting up Call Center AI Analyst\n")
    create_database()
    build_vectorstore()
    print("\nDone!\n")