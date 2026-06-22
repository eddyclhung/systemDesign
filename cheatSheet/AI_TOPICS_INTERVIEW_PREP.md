# Interview Prep: RAG, Agents, How You Use AI, Hallucination Handling

Study guide tied to **this project** (Player Service + Python ML + Ollama). Every concept below maps to code you can point at or live-implement.

---

## How to use this doc

1. Read each section’s **30-second answer** out loud once.
2. Skim **In this project** — know file names and one demo curl.
3. Practice **If they push** follow-ups.
4. Use the **cheat sheet** at the end the morning of the interview.

---

## 1. RAG (Retrieval-Augmented Generation)

### 30-second answer

> "RAG means: before the LLM answers, I **retrieve** facts from a source I trust (our H2 database), **inject** them into the prompt, and instruct the model to answer **only** from those facts. The LLM handles language; the database owns truth. I then **evaluate** the output programmatically with a faithfulness check."

### What RAG is NOT

- Not fine-tuning the model on player data
- Not asking the LLM to "know" baseball from its weights
- Not having the ML k-NN model write prose (it returns ids, not text)

### RAG pipeline (4 steps)

```
Retrieve → Augment prompt → Generate → Evaluate
```

| Step | This project |
|------|----------------|
| **Retrieve** | `PlayerRepository.findByLastName...`, `findAllById(member_ids)` |
| **Augment** | `FACTS:` block in `TeamChatService` summary prompt |
| **Generate** | `ChatClientService.chat(prompt, 0.1f)` via Ollama |
| **Evaluate** | `FaithfulnessEvaluator.evaluate(summary, teamNames)` |

### Prompt structure (why it matters)

```text
ROLE:     You are a baseball scout.
FACTS:    Seed player: Jim Abbott
          Team members: Jim Abbott, Pat Combs, ...
TASK:     Describe this team in 2-3 sentences. Mention every name.
CONSTRAINT: If a detail is not in FACTS, do not mention it.
```

Separating **facts** from **instructions** reduces the model treating its own knowledge as input data.

### Interview phrases

- "RAG grounds subjective generation in objective data."
- "Retrieval quality is the ceiling — garbage in, hallucination out."
- "I measure RAG with **faithfulness**: did the answer only use retrieved facts?"

### If they push

| Question | Answer |
|----------|--------|
| RAG vs fine-tuning? | RAG for fresh/structured DB data that changes; fine-tuning for style/domain when data is static and large |
| What if retrieval is wrong? | Wrong player seeded → wrong team → faithfulness can still be high but answer is wrong; fix **retrieval** (disambiguate Abbott) |
| Chunking / embeddings? | Not needed here — structured rows, not documents. For PDFs/wiki you'd embed + vector search |
| When is RAG not enough? | Multi-hop reasoning across many docs, or when facts aren't in retrievable form |

---

## 2. Agents

### 30-second answer

> "An **agent** is a system where an LLM **decides what action to take** — call a tool, query a DB, hit an API — rather than only returning text. In this project, the continuous chat is a **lightweight agent**: it classifies intent (generate team / give feedback / rebuild), dispatches to the right backend, and maintains **session memory** across turns."

### Agent vs plain chat

| Plain chat | Agent |
|------------|-------|
| Input → LLM → text | Input → **plan/route** → **tool(s)** → compose response |
| No side effects | Changes state (feedback exclusions, sessions) |
| Stateless | Often stateful (session, memory) |

### This project as an agent (tool map)

| User message | "Tool" invoked | Side effect |
|--------------|----------------|-------------|
| "Build a team like Abbott" | `PlayerRepository` + ML `/team/generate` + LLM summarize | New `ChatSession` |
| "Remove Combs" | ML `/team/feedback` + `/team/generate` + LLM summarize | `exclude_db` updated in Python |
| "Rebuild the team" | ML `/team/generate` + LLM summarize | Session updated |
| "Why is the sky blue?" | LLM only | None |

**Key line:** The LLM does **not** pick the team (ML does). The agent **orchestrates** specialists.

### Agent patterns to name

1. **Router / dispatcher** — keyword or LLM intent → switch on action (`TeamChatService.handle`)
2. **Tool calling** — structured API calls with typed inputs/outputs (`TeamFeedbackRequest`)
3. **Memory** — `ChatSessionStore` holds `predictionId`, roster (so user doesn't resend ids)
4. **ReAct-style loop** (stretch) — generate → evaluate faithfulness → retry with corrective feedback

### If they push

| Question | Answer |
|----------|--------|
| LLM-as-router vs rules? | Rules for demo reliability (tinyllama); LLM JSON intent + rules fallback in production |
| How do you prevent runaway agents? | Max retries (1), bounded tools, no arbitrary code execution |
| Agent metrics? | Router accuracy, tool success rate, latency per tool, session completion rate |
| Multi-agent? | Overkill here; one orchestrator + three backends is enough |

---

## 3. How You Use AI (your personal framework)

### 30-second answer

> "I use AI **only where language is the product** — summarizing, routing intent, explaining. Factual decisions and recommendations stay in **deterministic systems**: SQL for truth, k-NN for similarity. I wrap LLM calls like any flaky dependency: timeouts, low temperature for facts, structured prompts, automated evaluation, and a human feedback loop where it matters."

### The decision matrix (memorize this)

| Task | Use AI? | Use instead |
|------|---------|-------------|
| Which players are similar? | **No** | Python k-NN `/team/generate` |
| Look up player birth year? | **No** | `PlayerRepository` |
| Summarize a roster in prose? | **Yes** | LLM + RAG |
| Parse "remove Combs" intent? | **Maybe** | Rules now; LLM router later |
| Invent team if ML is down? | **Never** | 503 + clear error |

### Your stack in one sentence

**Java orchestrates, Python recommends, H2 stores truth, Ollama narrates.**

### Operational practices (say you do these)

- **Temperature by task** — 0.1 grounded summaries, 0.8 creative chat
- **Evaluation in the loop** — faithfulness score + retry below 0.8
- **Trace ids** — `predictionId` links inference to feedback; `sessionId` links chat turns
- **Golden set** — fixed prompts; regression-test prompt/model changes
- **Honest limits** — tinyllama is a demo floor; production needs bigger model or narrower scope

### If they push

| Question | Answer |
|----------|--------|
| When wouldn't you use AI? | Compliance-critical paths, pure lookup, math, when explainability must be exact |
| Build vs buy? | Ollama local for dev; managed API for prod if SLA/latency matter |
| Cost control? | Cache player data, minimize tokens in FACTS block, cap retries, small model for routing only |
| How do you stay current? | Prompts versioned like code; eval suite runs on every change |

---

## 4. Hallucination Handling

### 30-second answer

> "Hallucination is when the model states **confident falsehoods**. I handle it in layers: **prevent** (RAG + low temperature + strict prompt), **detect** (faithfulness evaluator + fabrication regex), **correct** (one retry with missing names), and **contain** (never let LLM choose roster members — ML + DB only)."

### Defense layers (in order)

```
Layer 1 PREVENT  → RAG facts block, "ONLY use facts below", temperature 0.1
Layer 2 CONSTRAIN → LLM never outputs player ids; ML+DB supply the list
Layer 3 DETECT   → FaithfulnessEvaluator (coverage + suspectedFabrications)
Layer 4 CORRECT  → Retry prompt listing missed names (score < 0.8)
Layer 5 CONTAIN  → Return team[] from DB even if summary is bad; summary is garnish
Layer 6 HUMAN    → Thumbs-down on recommendations; implicit quality signal
```

### What your evaluator catches vs misses

| Catches | Misses |
|---------|--------|
| Invented player names ("Babe Ruth" not in FACTS) | Wrong *attributes* ("retired", "aggressive") |
| Missing names from roster | Paraphrases that omit last names |
| | Correct-looking prose with subtle factual errors |

**Say this:** "Faithfulness here is **name coverage** — a strict subset of full factual accuracy. I'd extend checks to debut/bats/throws if those were in FACTS."

### Real example from your demo

First summary (loose prompt): invented "aggressive approach", "retired/active".

After structured FACTS + 0.1 temp + retry: less embellishment, measurable via `faithfulness.score` and `suspectedFabrications`.

### Golden set: measure and tune your hallucination defenses

Automated layers (RAG, evaluator, retry) are hypotheses until you **regression-test** them. A **golden set** is a fixed list of prompts + expected behavior you re-run after every prompt, temperature, or model change — same idea as unit tests for LLM output.

#### Step 1 — Define what "pass" means (quality bar)

For grounded team summaries, a case **passes** when all of these hold:

| Check | Pass criteria |
|-------|----------------|
| Coverage | `faithfulness.score >= 0.8` (or your chosen threshold) |
| Fabrication | `suspectedFabrications` is empty |
| Constraint | Summary mentions every name in `team[]` |
| Containment | `team[]` itself came from ML+DB, not the LLM (always true in your architecture) |

Optional human spot-check: summary is readable and doesn't invent attributes ("retired", "aggressive") even when name coverage is 1.0.

#### Step 2 — Build the golden set (10–20 cases)

Mix **happy path**, **edge cases**, and **known failure modes**:

| # | Input prompt | What you're testing |
|---|--------------|---------------------|
| 1 | `Build a team like Abbott` | Baseline RAG summary |
| 2 | `Build a team like Aaron` | Common name, many matches |
| 3 | `Build a team like McGriff` | Single clear seed |
| 4 | Same as #1, run 3× | Consistency at temp 0.1 |
| 5 | `Build a team like Abbott` with loose prompt (A/B) | Before/after FACTS block |
| 6 | Team of 5 with one hard-to-spell name | Coverage stress test |
| 7 | Generic: `Why is the sky blue?` | No faithfulness gate (control) |

Store as JSON or a test class — inputs are stable; **outputs are scored**, not exact-string matched (LLM wording varies).

Example record:

```json
{
  "prompt": "Build a team like Abbott",
  "expectAction": "TEAM_GENERATE",
  "minFaithfulness": 0.8,
  "maxFabrications": 0
}
```

#### Step 3 — Run the suite and record metrics

After each change (prompt edit, temperature, retry threshold, model swap):

1. Call `POST /v1/chat` for each golden prompt (fixed seed player if possible).
2. Record per case: `faithfulness.score`, `suspectedFabrications`, latency, retry fired (yes/no).
3. Compute **pass rate** = cases meeting all criteria / total cases.

Log to a spreadsheet or `ai_metric` lines — you want trends over time, not one-off eyeballing.

#### Step 4 — Inspect failures and tune the right knob

| What you see | Likely cause | Fix |
|--------------|--------------|-----|
| Low coverage, no fabrications | Prompt doesn't demand all names; or "exactly 2 sentences" too tight | Add "mention every name"; relax to 2–3 sentences |
| `suspectedFabrications` non-empty | Model inventing players | Tighten FACTS constraint; lower temp; add fabrication gate (fail/retry if non-empty) |
| Coverage 1.0 but prose invents attributes | Evaluator too narrow | Extend FACTS with debut/bats; add attribute-level checks or human review |
| Pass rate OK but retries fire 80% of the time | Threshold too strict or prompt weak | Fix prompt first; only then lower `RETRY_SCORE_THRESHOLD` from 0.8 |
| Pass rate low, summaries look fine | Evaluator too strict (e.g. last-name matching) | Fix metric before loosening bar |
| Pass rate drops after model change | New model ignores instructions | Re-tune temp + prompt; consider rules-first for facts |

**Key principle:** tune the **quality bar** from failure analysis, not vibes. The bar is the lowest score where outputs are good enough on the golden set at acceptable latency/cost.

#### Step 5 — Lock it in (regression gate)

- Treat prompt text like code: version it, review it, run the golden set in CI or before demo.
- Any change that drops pass rate below an agreed floor (e.g. 90%) blocks merge until fixed or the bar is consciously revised.
- Complement automation with periodic human review — catches Goodhart cases (coverage 1.0, useless prose).

#### How this connects to your code today

| Golden set check | Code hook |
|------------------|-----------|
| Coverage | `FaithfulnessEvaluator.evaluate()` → `score` |
| Fabrications | `suspectedFabrications` list |
| Auto-correct | `RETRY_SCORE_THRESHOLD = 0.8` + retry block in `TeamChatService` |
| Prevent | FACTS/TASK prompt + `chat(prompt, 0.1f)` |

**Interview line:** *"Hallucination handling isn't a one-time prompt tweak — I regression-test it. Golden set pass rate is how I know whether Layer 3–4 actually work after a change."*

### If they push

| Question | Answer |
|----------|--------|
| Can low temperature eliminate hallucination? | No — makes wrong answers **consistent**. Need RAG + verification |
| LLM-as-judge to detect hallucination? | Possible with bigger model; risk: judge hallucinates too. Prefer deterministic checks when facts are structured |
| Goodhart's law? | Model could list all names with nonsense between — coverage 1.0, useless text; need fluency + human eval too |
| Production gate? | Block response if `suspectedFabrications` non-empty; or return team without LLM summary |
| How do you tune the 0.8 threshold? | Sweep 0.6–1.0 on golden set; pick lowest value with ≥90% pass rate and acceptable retry rate |

---

## 5. Tie it all together (one story for the AI session)

Use this **60-second narrative** linking all four topics:

> "The user asks for a team in natural language — that's an **agent** routing problem. I retrieve the seed player from our DB and similar players from the k-NN service — that's **retrieval**, not generation. I pass only those names into the LLM in a FACTS block — that's **RAG**. I use low temperature and a faithfulness check to handle **hallucination**; if coverage is low, I retry once with corrective feedback. When the user says 'remove Combs', the agent remembers the session, calls `/team/feedback`, and regenerates — **how I use AI** is: language and routing only; recommendations and truth stay in ML and SQL."

---

## 6. Live demo script (2 minutes)

```bash
# 1. RAG + agent generate
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Build a team like Abbott"}'
# Point at: team[] from ML+DB, summary from LLM, faithfulness.score

# 2. Agent memory + feedback tool
curl -X POST http://localhost:8080/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"<from above>","prompt":"Remove Combs"}'
# Point at: action=TEAM_FEEDBACK, rejectedMember, roster changed

# 3. Hallucination talking point
# If suspectedFabrications non-empty in response, explain detection + retry
```

---

## 7. Cheat sheet (morning-of)

| Topic | One line |
|-------|----------|
| **RAG** | Retrieve from DB → FACTS prompt → generate → faithfulness eval |
| **Agent** | Route intent → call tools (ML, DB, LLM) → session memory |
| **How I use AI** | Language + routing only; ML + SQL own facts and recommendations |
| **Hallucination** | Prevent → detect → correct → contain; **golden set** regression-tests pass rate |

| File to cite | Topic |
|--------------|-------|
| `TeamChatService.java` | Agent orchestration, RAG prompt, retry loop |
| `FaithfulnessEvaluator.java` | Hallucination detection |
| `ChatSessionStore.java` | Agent memory |
| `player-service-model/server.py` | ML tool (not LLM) |
| `ChatClientService.java` | Temperature, Ollama call |

---

## 8. Questions to ask them (shows maturity)

- "Is the eval session focused on **building** the flow or **defending** design tradeoffs?"
- "Are we expected to use the local tinyllama or is discussing a production model swap in scope?"
- "Should feedback loop persistence be in scope, or is in-memory exclusion acceptable for the exercise?"
