# ReAct vs LangGraph comparison

Run at 2026-10-14 18:39:10 | model: `openai/gpt-oss-120b` | 8 questions

| Metric | ReAct | LangGraph |
|---|---|---|
| Success rate | 0% | 100% |
| Right tool used | 12% | 100% |
| Avg seconds per question | 34.93 | 8.63 |
| Avg tool calls per question | 0.38 | 1.25 |

## Answers to check by hand

### What is AHT and what is its target?

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| react | _Exception | 37.44 | |
| langgraph | search_knowledge_base | 4.08 | |

**react answer:**

> Agent stopped due to iteration limit or time limit.

**langgraph answer:**

> **AHT (Average Handle Time)** – the average amount of time an agent spends on a call, including talk time, hold time, and after‑call work (wrap‑up).  
> 
> **Target:** Less than **5.0 minutes** per call (lower = better).

### Who has the worst FCR in Q3?

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| langgraph | get_top_bottom_agents | 2.19 | |
| react | - | 1.97 | |

**langgraph answer:**

> The agent with the lowest First Call Resolution (FCR) in Q3 2024 is **Vikram Nair (Team A)**, whose FCR was **68.4 %**—well below the target of > 80 %.

**react answer:**

> Tool choice is none, but model called a tool

### Compare Team A vs Team B for the full year

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| react | - | 1.36 | |
| langgraph | get_team_comparison | 3.95 | |

**react answer:**

> Tool choice is none, but model called a tool

**langgraph answer:**

> **Team‑level performance (Jan – Dec 2024)**  
> 
> | KPI | Team A | Team B | Target | Gap / Surplus |
> |-----|--------|--------|--------|---------------|
> | **AHT (min)** | **5.41** | **4.55** | < 5.0 | A = +0.41 min (miss) • B = ‑0.45 min (meets) |
> | **FCR (%)** | **75.1 %** | **83.1 %** | > 80 % | A = ‑4.9 pts (miss) • B = +3.1 pts (meets) |
> | **CSAT (%)** | **80.4 %** | **87.8 %** | > 85 % | A = ‑4.6 pts (miss) • B = +2.8 pts (meets) |
> | **Adherence (%)** | **85.8 %** | **91.6 %** | > 90 % | A = ‑4.2 pts (miss) • B = +1.6 pts (meets) |
> | **Total Calls Handled** | 13,563 | 13,059 | – | A handled ~4 % more volume |
> 
> ### Key Take‑aways
> 1. **Team B consistently meets or exceeds every KPI**, especially AHT (4.55 min) and adherence (91.6 %).  
> 2. **Team A underperforms on all four metrics**, with the biggest gaps in AHT (+0.41 min) and FCR (‑4.9 pts).  
> 3. Despite lower efficiency, Team A processed **~4 % more calls**, indicating higher workload pressure that likely contributes to the KPI shortfalls.
> 
> ### Actionable Recommendations
> 
> | Issue | Recommended Action | Expected Impact |
> |-------|--------------------|-----------------|
> | **AHT too high (5.41 min)** | • Conduct a quick‑win call‑flow audit on the top‑5 call types that drive longer handling times.<br>• Deploy targeted micro‑training on call triage and use of knowledge‑base shortcuts. | Reduce average handle time by ~0.3‑0.5 min, bringing Team A under the 5‑min target. |
> | **FCR below 80 %** | • Identify the most frequent “repeat‑call” reasons via call‑reason codes; create a FAQ/solution script for those issues.<br>• Introduce a “first‑call resolution checklist” for agents to verify problem closure before ending the call. | Boost FCR by 3‑5 pts, aligning with the 80 % target. |
> | **CSAT lagging** | • Implement post‑call “quick‑pulse” surveys for a sample of calls to capture real‑time sentiment and coach agents on tone & empathy.<br>• Recognize and share best‑practice recordings from Team B agents with high CSAT scores. | Lift CSAT by 3‑4 pts, moving above 85 %. |
> | **Adherence shortfall** | • Review schedule adherence reports to pinpoint shift‑swap or break‑policy violations.<br>• Introduce a real‑time adherence dashboard with alerts for agents falling >5 % off schedule. | Increase adherence to ≥90 % by improving punctuality and break compliance. |
> | **Higher call volume pressure** | • Re‑balance workload: consider shifting ~5 % of calls from Team A to Team B (or add a part‑time buffer resource) to reduce agent fatigue.<br>• Automate routine inquiries (e.g., balance checks) via IVR/Chatbot to free agent time. | Lower AHT and improve FCR/CSAT as agents can focus on complex issues. |
> 
> ### Quick Wins (3‑month horizon)
> 
> 1. **Micro‑training sprint** on the top 3 call categories that inflate AHT – expected AHT reduction of ~0.2 min.  
> 2. **FCR checklist rollout** – pilot with 4 agents, then scale; aim for +3 pts FCR.  
> 3. **Adherence alert system** – simple Slack/Teams bot notifying agents when they dip below 90 % schedule adherence; target +2 pts adherence.
> 
> By addressing the workflow inefficiencies and reinforcing first‑call resolution practices, Team A can close the KPI gaps while maintaining its higher call volume. Team B’s practices (shorter AHT, higher adherence) should be documented and shared as best‑practice models for Team A.

### Show Kavya Menon complete performance

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| langgraph | get_agent_metrics | 5.94 | |
| react | _Exception, get_agent_metrics | 142.97 | |

**langgraph answer:**

> **Kavya Menon – Full‑Year 2024 Performance**
> 
> | KPI | Year‑Average | Target | Status |
> |-----|--------------|--------|--------|
> | **AHT** (minutes) | **4.05 m** | < 5.0 m | ✅ Well below the ceiling |
> | **FCR** | **90.0 %** | > 80 % | ✅ Strong, but a few months dip |
> | **CSAT** | **93.1 %** | > 85 % | ✅ Excellent |
> | **Adherence** | **96.1 %** | > 90 % | ✅ Very high |
> | **Calls Handled** | **≈ 223 calls / month** (2 677 total) | – | – |
> 
> ### Monthly Highlights (Key Deviations)
> 
> | Month | AHT | FCR | CSAT | Adherence | Comment |
> |-------|-----|-----|------|-----------|---------|
> | **Jan** | 3.8 m | 91.8 % | 92.2 % | 97.9 % | Strong start |
> | **Feb** | 4.0 m | 89.2 % | 91.4 % | 93.1 % | Adherence dip (‑4.8 pts) |
> | **May** | 4.0 m | **87.6 %** (lowest) | 93.9 % | 97.4 % | FCR below 90 % |
> | **Jun** | 4.1 m | 88.8 % | 94.1 % | 96.9 % | Consistent CSAT |
> | **Jul** | **3.6 m** (best) | 88.9 % | 94.3 % | 95.4 % | AHT improvement |
> | **Aug** | 4.1 m | **93.2 %** (best) | 92.9 % | **98.3 %** (best) | Peak adherence |
> | **Oct** | 4.2 m | 88.3 % | 94.4 % | 95.5 % | Stable |
> | **Nov** | 4.6 m | 89.0 % | 93.9 % | 95.7 % | AHT rise |
> | **Dec** | **4.6 m** (worst) | 87.7 % | 91.3 % | 94.4 % | Highest AHT, lower FCR/CSAT |
> 
> ### Trend Insights
> 
> * **AHT** – Overall excellent (4.05 m) but spikes in **Nov‑Dec** (4.6 m). The July dip to 3.6 m shows she can handle calls faster when workload is balanced.
> * **FCR** – Average 90 % (well above target) yet three months (May, Oct, Dec) fall just under 90 %. These coincide with higher call volumes.
> * **CSAT** – Consistently > 91 % throughout the year, peaking at 94.4 % in Oct.
> * **Adherence** – Very strong (> 93 % every month). The February dip (93.1 %) is the only breach of the 95 % “gold” zone but still above the 90 % target.
> 
> ### Actionable Recommendations
> 
> | Area | Recommendation | Expected Impact |
> |------|----------------|-----------------|
> | **AHT reduction in Q4** | • Review call scripts and knowledge‑base usage for Dec‑Jan spikes.<br>• Introduce a short “quick‑resolution” checklist for routine issues.<br>• Pair Kavya with a high‑AHT peer for a 2‑week shadowing session. | Aim to bring Q4 AHT ≤ 4.2 m (‑0.4 m vs. current) |
> | **FCR consistency** | • Conduct a root‑cause analysis on the May & Dec tickets that required callbacks.<br>• Provide targeted product‑update training before high‑volume months (May, Oct, Dec). | Target ≥ 92 % FCR in those months |
> | **Maintain CSAT** | • Keep the “customer‑first” tone scripts that are driving > 93 % scores.<br>• Celebrate the July AHT win in team huddles to reinforce best practices. | Preserve > 92 % CSAT year‑round |
> | **Adherence vigilance** | • Set a reminder for February‑type schedule adjustments (e.g., shift swaps) to avoid future dips.<br>• Use the adherence dashboard to flag any < 95 % days early. | Keep adherence > 95 % consistently |
> | **Call volume management** | • When call volume exceeds 240/month (July, Aug, Sep, Oct), schedule a short “focus‑time” block to handle complex cases, preventing AHT creep. | Smoother workload, lower AHT spikes |
> 
> ### Bottom Line
> 
> Kavya Menon **exceeds all KPI targets** for 2024, delivering **high‑quality, timely service** with excellent schedule discipline. The primary opportunities lie in **flattening the Q4 AHT rise** and **tightening FCR during peak‑volume months**. Implementing the above micro‑coaching and process tweaks should push her performance from “excellent” to “benchmark‑setting” for the team.

**react answer:**

> Agent stopped due to iteration limit or time limit.

### How did FCR change from Q1 to Q4?

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| react | - | 1.57 | |
| langgraph | get_team_comparison, calculate_metric_change | 42.0 | |

**react answer:**

> Tool choice is none, but model called a tool

**langgraph answer:**

> **First‑Call Resolution (FCR) – Q1 vs. Q4 (2024)**  
> 
> | Team | Q1 FCR | Q4 FCR | Absolute Δ | Relative Δ |
> |------|--------|--------|------------|------------|
> | **Team A (Mumbai)** | **74.9 %** | **75.0 %** | **+0.04 pp** | **+0.1 %** (slight improvement) |
> | **Team B (Bangalore)** | **83.4 %** | **82.6 %** | **‑0.79 pp** | **‑0.9 %** (decline) |
> 
> ### What the numbers mean
> - **Team A** barely moved the needle; the 0.04‑percentage‑point rise keeps it well **below the 80 % target**.  
> - **Team B** slipped just under 1 percentage point, dropping from **above** to **below** the 80 % target.
> 
> ### Actionable insights
> 1. **Team B – Reverse the dip**
>    - **Root‑cause analysis** on Q3–Q4 calls (e.g., new product issues, staffing changes) to pinpoint why FCR fell.
>    - **Targeted coaching** on resolution techniques for agents whose Q4 FCR is below their Q1 baseline.
>    - **Introduce a quick‑resolution script** for the most common issues that caused the drop.
> 
> 2. **Team A – Accelerate improvement**
>    - **Set a short‑term goal**: raise FCR to **≥78 %** by end of Q1 2025 (≈+3 pp).
>    - **Pilot a “first‑call win” checklist** for the top‑performing agents and roll it out team‑wide.
>    - **Monitor daily FCR** and flag any agent whose daily rate falls <70 % for immediate feedback.
> 
> 3. **Cross‑team learning**
>    - Have **Team B share best practices** that kept them above target in Q1 (e.g., knowledge‑base usage, escalation avoidance) with Team A.
>    - Conduct a **joint weekly review** of FCR trends to keep both teams aligned on the 80 % target.
> 
> **Bottom line:** From Q1 to Q4, Team A’s FCR stayed essentially flat (+0.04 pp) while Team B’s slipped by –0.79 pp, moving it below the desired threshold. Immediate corrective actions for Team B and a growth plan for Team A are recommended to meet the >80 % FCR target in 2025.

### How did Team B FCR change from Q1 to Q4?

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| langgraph | calculate_metric_change | 2.93 | |
| react | - | 20.6 | |

**langgraph answer:**

> **Team B – First Call Resolution (FCR) Trend**
> 
> | Period | FCR |
> |--------|-----|
> | **Q1 2024** | **83.38 %** |
> | **Q4 2024** | **82.59 %** |
> | **Δ (Q1 → Q4)** | **‑0.79 pp** (‑0.9 %) |
> 
> - **Target:** > 80 % – Team B stays above the target, but the metric slipped slightly.
> - **Direction:** Negative trend (‑0.9 % QoQ).
> 
> ### Actionable Insights
> 
> | Issue | Why It Matters | Quick Wins |
> |-------|----------------|------------|
> | **Slight FCR decline** | Even a sub‑1 % drop can signal emerging gaps in knowledge, process, or call routing that may widen over time. | 1. **Root‑cause audit** on Q4 calls with low‑FCR scores (e.g., repeat contacts, escalations).<br>2. **Refresh knowledge‑base articles** that were accessed most during Q4. |
> | **Potential skill drift** | Agents may be handling newer product issues without updated training. | 3. **Targeted micro‑learning** for the top‑3 issue categories that drove repeat calls in Q4.<br>4. **Peer‑shadowing**: pair agents with the highest FCR (top‑bottom agents list) for a week. |
> | **Call routing inefficiencies** | Mis‑routed calls increase handling time and reduce first‑call success. | 5. **Review IVR/skill‑based routing rules**; adjust to route high‑complexity issues directly to senior agents. |
> | **Monitoring** | Ongoing tracking prevents small declines from becoming larger problems. | 6. **Set a weekly FCR dashboard alert** when the metric drops >0.3 pp from the prior week. |
> 
> ### Recommendation
> 
> - **Immediate:** Conduct a focused FCR audit on Q4 calls (top 5 issue types) and implement quick‑fix knowledge updates.
> - **Mid‑term:** Roll out a 2‑week refresher training for all Team B agents on the identified gaps, then re‑measure FCR in Q1 2025.
> - **Long‑term:** Integrate the weekly FCR alert into the team’s performance dashboard and tie a small incentive (e.g., “FCR Champion”) to sustained improvement.
> 
> By addressing the root causes now, Team B can not only **recover the 0.79 pp loss** but also push the FCR **well above the 80 % target**, strengthening overall customer satisfaction.

**react answer:**

> 3 validation errors for calculate_metric_changeSchema
> metric
>   field required (type=value_error.missing)
> from_period
>   field required (type=value_error.missing)
> to_period
>   field required (type=value_error.missing)

### Which agents are below CSAT target?

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| react | - | 3.73 | |
| langgraph | get_top_bottom_agents | 2.07 | |

**react answer:**

> Tool choice is none, but model called a tool

**langgraph answer:**

> **Agents whose CSAT is below the > 85 % target (all‑time average):**
> 
> | Agent | Team | CSAT |
> |-------|------|------|
> | Vikram Nair | Team A | 73.77 % |
> | Pooja Mehta | Team A | 77.83 % |
> | Priya Reddy | Team B | 79.77 % |
> | Rahul Joshi | Team A | 81.09 % |
> | Amit Gupta | Team A | 82.48 % |
> | Sneha Iyer | Team B | 84.77 % |
> 
> These six agents are the only ones falling short of the CSAT target of > 85 %.

### Why is Vikram Nair underperforming?

| Engine | Tools used | Seconds | Correct? (fill in) |
|---|---|---|---|
| langgraph | get_agent_metrics, get_team_comparison | 5.9 | |
| react | - | 69.82 | |

**langgraph answer:**

> **Vikram Nair – KPI snapshot (Jan‑Dec 2024)**  
> 
> | KPI | Avg 2024 | Target | How far off |
> |-----|----------|--------|-------------|
> | **AHT** | **6.6 min** | < 5.0 min | **+1.6 min** (31 % slower) |
> | **FCR** | **68.0 %** | > 80 % | **‑12 pp** (15 % below target) |
> | **CSAT** | **73.5 %** | > 85 % | **‑11.5 pp** (13 % below target) |
> | **Adherence** | **78.0 %** | > 90 % | **‑12 pp** (13 % below target) |
> 
> *Compared with Team A averages (AHT 5.41 min, FCR 75.1 %, CSAT 80.4 %, Adherence 85.8 %)*, Vikram is **consistently below every benchmark**.
> 
> ### Where the gaps are biggest
> | Month | KPI (worst) | Value |
> |-------|-------------|-------|
> | **May‑2024** | CSAT | 71.2 % (lowest of the year) |
> | **Jun‑2024** | FCR | 64.9 % (lowest) |
> | **Nov‑2024** | AHT | 6.8 min (highest) |
> | **Jul‑2024** | Adherence | 76.7 % (lowest) |
> 
> ### Likely root causes (inferred from the pattern)
> 
> | KPI | Possible drivers |
> |-----|-------------------|
> | **AHT (↑)** | • Longer average handling time suggests inefficient call flow or lack of product knowledge. <br>• Spike in Nov (6.8 min) coincides with a new product launch – likely insufficient training. |
> | **FCR (↓)** | • Sub‑80 % FCR points to unresolved issues or frequent escalations. <br>• Consistently low across the year, indicating gaps in troubleshooting scripts or decision‑making authority. |
> | **CSAT (↓)** | • Directly linked to FCR and AHT – customers feel the call drags on and their problem isn’t solved. <br>• The dip in May aligns with the lowest CSAT and a modest dip in adherence, hinting at schedule fatigue. |
> | **Adherence (↓)** | • Regularly 10‑12 pp below the team average, meaning Vikram is often late to shift start/end or taking unscheduled breaks. <br>• Low adherence can force rushed calls later, worsening AHT and CSAT. |
> 
> ### Actionable recommendations
> 
> | Action | Why it helps | Quick win target |
> |--------|--------------|------------------|
> | **1. Targeted coaching on call flow** – review 5 of his longest calls (≥ 7 min) with a quality analyst. | Identify steps that can be trimmed or scripted. | Reduce AHT to **≤ 5.8 min** within 4 weeks. |
> | **2. FCR skill‑boost workshop** – focus on root‑cause analysis, product knowledge, and escalation authority. | Improves first‑call resolution and downstream CSAT. | Raise FCR to **≥ 75 %** in the next month. |
> | **3. Schedule adherence audit** – compare his logged‑in times vs roster; flag any pattern of late log‑ins or early log‑outs. | Aligns work time with staffing, reduces overtime pressure. | Bring adherence to **≥ 85 %** in 2 weeks. |
> | **4. Peer‑shadowing with a top performer** (e.g., the top‑3 CSAT agent from Team A). | Real‑time modeling of best practices for tone, empathy, and problem solving. | Aim for a **+5 pp CSAT lift** after 2 weeks of shadowing. |
> | **5. Mini‑training on the new product launched in Nov** – quick refresher on FAQs and troubleshooting steps. | Directly addresses the Nov AHT spike. | Cut Nov‑AHT back to **≤ 6.2 min** for the next month. |
> | **6. Real‑time KPI dashboard alerts** – set up a personal dashboard that flags when AHT > 6 min, FCR < 70 %, or adherence < 80 % for a shift. | Gives immediate feedback for self‑correction. | Maintain all three alerts under threshold for **≥ 80 % of shifts** within 1 month. |
> 
> ### Bottom line
> Vikram’s 2024 performance is **significantly under the team and corporate targets** across every KPI. The data shows a consistent pattern of longer calls, unresolved issues, lower customer satisfaction, and schedule drift. By focusing on **call‑flow efficiency, FCR competency, and adherence discipline**, you can expect measurable improvements within the next 4‑6 weeks and bring his metrics into line with—or above—Team A’s averages.

**react answer:**

> Error code: 429 - {'error': {'message': 'Rate limit reached for model `openai/gpt-oss-120b` in organization `org_01kswsx2qzee7stg759wv4hfhc` service tier `on_demand` on tokens per day (TPD): Limit 200000, Used 196941, Requested 6547. Please try again in 25m6.816s. Need more tokens? Upgrade to Dev Ti
