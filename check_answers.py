"""
check_answers.py
----------------
Prints the TRUE numbers straight from cc_database.db (plain SQL, no AI, no
agent tools) so you can fill in the "Correct?" column of engine_comparison.md.

It only READS the database. It changes nothing.

Run from the CallCenter folder:
    python check_answers.py
"""

import sqlite3

DB = "cc_database.db"
Q = {
    "Q1": ["Jan-2024", "Feb-2024", "Mar-2024"],
    "Q2": ["Apr-2024", "May-2024", "Jun-2024"],
    "Q3": ["Jul-2024", "Aug-2024", "Sep-2024"],
    "Q4": ["Oct-2024", "Nov-2024", "Dec-2024"],
}

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row


def q(sql, params=()):
    return conn.execute(sql, params).fetchall()


def marks(months):
    return ",".join("?" * len(months))


def title(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


# 1 ---------------------------------------------------------------------
title('1) "Who has the worst FCR in Q3?"   (lowest average FCR, Jul-Sep 2024)')
rows = q(
    f"SELECT agent_name, team, ROUND(AVG(fcr),2) AS fcr FROM performance "
    f"WHERE month_year IN ({marks(Q['Q3'])}) GROUP BY agent_name, team ORDER BY fcr ASC LIMIT 3",
    Q["Q3"],
)
for r in rows:
    print(f"   {r['agent_name']:<16} {r['team']:<7} FCR {r['fcr']}%")
print("   The agent said: Vikram Nair (Team A) 68.4%")

# 2 ---------------------------------------------------------------------
title('2) "Compare Team A vs Team B for the full year"')
for r in q("SELECT team, ROUND(AVG(aht),2) a, ROUND(AVG(fcr),1) f, ROUND(AVG(csat),1) c, "
           "ROUND(AVG(adherence),1) d, SUM(calls_handled) t FROM performance GROUP BY team ORDER BY team"):
    print(f"   {r['team']}: AHT {r['a']} | FCR {r['f']} | CSAT {r['c']} | Adherence {r['d']} | Calls {r['t']}")
print("   The agent said: A = 5.41 / 75.1 / 80.4 / 85.8 / 13,563   B = 4.55 / 83.1 / 87.8 / 91.6 / 13,059")

# 3 ---------------------------------------------------------------------
title('3) "Show Kavya Menon complete performance"   (full-year averages)')
r = q("SELECT agent_name, ROUND(AVG(aht),2) a, ROUND(AVG(fcr),1) f, ROUND(AVG(csat),1) c, "
      "ROUND(AVG(adherence),1) d, SUM(calls_handled) t, COUNT(*) n FROM performance "
      "WHERE LOWER(agent_name) LIKE '%kavya%'")[0]
if r["agent_name"]:
    print(f"   {r['agent_name']}: AHT {r['a']} | FCR {r['f']} | CSAT {r['c']} | Adherence {r['d']} | "
          f"Calls {r['t']} over {r['n']} months")
    print("   The agent said: AHT 4.05 | FCR 90.0 | CSAT 93.1 | Adherence 96.1 | Calls 2,677")
    print("   Her lowest-FCR month and highest-AHT month:")
    low = q("SELECT month_year, fcr FROM performance WHERE LOWER(agent_name) LIKE '%kavya%' ORDER BY fcr ASC LIMIT 1")[0]
    high = q("SELECT month_year, aht FROM performance WHERE LOWER(agent_name) LIKE '%kavya%' ORDER BY aht DESC LIMIT 1")[0]
    print(f"      lowest FCR: {low['month_year']} {low['fcr']}%   |   highest AHT: {high['month_year']} {high['aht']} min")
    print("   The agent said: lowest FCR = May 87.6%, highest AHT = Dec 4.6")
else:
    print("   Kavya not found in the database")

# 4 ---------------------------------------------------------------------
title('4) "How did FCR change from Q1 to Q4?"   (by team, and both quarters vs the 80% target)')
for team in ("Team A", "Team B"):
    vals = {}
    for quarter in ("Q1", "Q4"):
        vals[quarter] = q(
            f"SELECT ROUND(AVG(fcr),2) f FROM performance WHERE team=? AND month_year IN ({marks(Q[quarter])})",
            (team, *Q[quarter]),
        )[0]["f"]
    delta = round(vals["Q4"] - vals["Q1"], 2)
    status = lambda v: "ABOVE 80% target" if v > 80 else "BELOW 80% target"
    print(f"   {team}: Q1 {vals['Q1']} ({status(vals['Q1'])})  ->  Q4 {vals['Q4']} ({status(vals['Q4'])})   change {delta:+}")
print("   The agent said Team B 'dropped from above to below the 80% target'. Compare with the line above.")

# 5 ---------------------------------------------------------------------
title('5) "Which agents are below CSAT target?"   (all-time average CSAT < 85)')
rows = q("SELECT agent_name, team, ROUND(AVG(csat),2) c FROM performance GROUP BY agent_name, team ORDER BY c ASC")
below = [r for r in rows if r["c"] < 85]
for r in rows:
    flag = "  <-- below 85" if r["c"] < 85 else ""
    print(f"   {r['agent_name']:<16} {r['team']:<7} CSAT {r['c']}{flag}")
print(f"   Agents below target: {len(below)}   (the agent said exactly 6)")

# 6 ---------------------------------------------------------------------
title('6) "Why is Vikram Nair underperforming?"   (full-year averages)')
r = q("SELECT agent_name, ROUND(AVG(aht),2) a, ROUND(AVG(fcr),2) f, ROUND(AVG(csat),2) c, "
      "ROUND(AVG(adherence),2) d FROM performance WHERE LOWER(agent_name) LIKE '%vikram%'")[0]
if r["agent_name"]:
    print(f"   {r['agent_name']}: AHT {r['a']} | FCR {r['f']} | CSAT {r['c']} | Adherence {r['d']}")
    print("   The agent said: AHT 6.6 | FCR 68.0 | CSAT 73.5 | Adherence 78.0")
    print("   (Question 5's list said his CSAT is 73.77. Only one of 73.5 / 73.77 can be right.)")
    nov = q("SELECT aht FROM performance WHERE LOWER(agent_name) LIKE '%vikram%' AND month_year='Nov-2024'")
    if nov:
        print(f"   Nov-2024 AHT: {nov[0]['aht']}   (the agent said 6.8)")
else:
    print("   Vikram not found in the database")

print("\nNote: nothing in this database says anything about a 'new product launch' in November.")
print("If an answer claims one, that statement did not come from your data.\n")
conn.close()
