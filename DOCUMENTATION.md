# FinLit Assistant — Project Documentation

A complete technical write-up of the financial-literacy chatbot: what it does, how it is
built, why each choice was made, how to run and deploy it, and a prepared question-and-answer
section for the presentation viva.

**Contents**

1. [Project summary](#1-project-summary)
2. [Problem statement and objectives](#2-problem-statement-and-objectives)
3. [What is RAG and why it is used here](#3-what-is-rag-and-why-it-is-used-here)
4. [System architecture and data flow](#4-system-architecture-and-data-flow)
5. [Technology stack — every component and why](#5-technology-stack--every-component-and-why)
6. [Repository layout](#6-repository-layout)
7. [File-by-file walkthrough](#7-file-by-file-walkthrough)
8. [The knowledge base](#8-the-knowledge-base)
9. [How retrieval works — the maths, explained simply](#9-how-retrieval-works--the-maths-explained-simply)
10. [The language-model call and prompt design](#10-the-language-model-call-and-prompt-design)
11. [Guardrails and safety](#11-guardrails-and-safety)
12. [Running the project](#12-running-the-project)
13. [Deployment](#13-deployment)
14. [Testing strategy](#14-testing-strategy)
15. [Cost, limits and performance](#15-cost-limits-and-performance)
16. [Limitations and future work](#16-limitations-and-future-work)
17. [Presentation Q&A — likely questions and answers](#17-presentation-qa--likely-questions-and-answers)
18. [Glossary of technical terms](#18-glossary-of-technical-terms)

---

## 1. Project summary

**FinLit Assistant** is a web chatbot that answers questions about personal finance and
banking — terms, products, and how things work — in plain language. It is aimed at improving
financial literacy.

Instead of relying on the language model's memory (which can be wrong or out of date), every
answer is **grounded** in a curated knowledge base of finance notes using a technique called
**Retrieval-Augmented Generation (RAG)**. The bot retrieves the most relevant passages from
that knowledge base and asks the language model to answer *using only those passages*, and it
shows the user which sources it used.

- **Interface:** a Streamlit web app (chat UI).
- **Language model + embeddings:** Google Gemini (free tier).
- **Knowledge base:** 9 hand-written Markdown topics (~5,000+ words), India-leaning.
- **Hosting:** Streamlit Community Cloud, deployed free from GitHub.

The project is inspired by the World Bank's
[WhatsApp-RAG-Example](https://github.com/worldbank/WhatsApp-RAG-Example), re-implemented as a
lighter, browser-based app.

---

## 2. Problem statement and objectives

**Problem.** Many people lack confidence with basic financial vocabulary and concepts
(EMI, credit score, NEFT vs RTGS, fixed deposit, mutual fund, KYC). General chatbots can
answer, but they may hallucinate figures or rules, give no sources, and drift into giving
risky personalised advice.

**Objectives.**

1. Answer financial-literacy questions accurately and consistently.
2. Ground answers in a known, reviewable body of content, and cite it.
3. Refuse to give personalised investment/tax/legal advice; stay educational.
4. Be cheap to run and easy to host and present from any laptop.
5. Be simple enough to explain end to end.

---

## 3. What is RAG and why it is used here

A large language model (LLM) answers from patterns learned during training. Two problems:

- **Hallucination** — it can state wrong facts confidently.
- **Staleness / no provenance** — you can't see *where* an answer came from, and its
  training data has a cutoff.

**Retrieval-Augmented Generation** fixes this by adding a retrieval step:

1. Keep a **knowledge base** of trusted text.
2. Convert each piece into a **vector embedding** (a list of numbers capturing meaning) and
   store it.
3. When a question arrives, embed the question too, find the knowledge-base pieces whose
   vectors are **most similar**, and paste that text into the prompt as *context*.
4. Instruct the LLM to answer **using that context**, and to say so when the context does not
   cover the question.

The LLM still does the language work (understanding the question, phrasing the answer), but
the *facts* come from your curated content. You can audit and edit the knowledge base without
retraining anything.

**Why RAG rather than the alternatives:**

| Approach | Why not (for this project) |
|---|---|
| Plain LLM, no retrieval | No grounding, no citations, higher hallucination risk. |
| Fine-tuning a model on finance data | Expensive, slow, needs ML expertise and a large dataset; hard to update; still no citations. |
| Big hard-coded FAQ / rule engine | Rigid; only answers exact matches; no natural-language understanding. |
| RAG (chosen) | Cheap, updatable by editing Markdown, gives sources, low hallucination, easy to explain. |

---

## 4. System architecture and data flow

### Build-time (offline, run once via `python ingest.py`)

```
knowledge_base/*.md
      │  read files
      ▼
  split into ~1,200-character chunks (with 200-char overlap)      [ingest.py]
      │
      ▼
  embed each chunk with Gemini  (model: gemini-embedding-001,     [common.embed_texts]
      │                          768 dimensions, unit-normalised)
      ▼
  store/embeddings.npy   (NumPy float32 matrix, 61 x 768)
  store/chunks.json      (the chunk text + {source, topic, chunk_index})
```

### Query-time (every user message)

```
user question  ─────────────────────────────────────────────┐
      │                                                      │
      ▼                                                      │
 embed question  (gemini-embedding-001, 768-d, normalised)   │   [rag.retrieve]
      │                                                      │
      ▼                                                      │
 cosine similarity = matrix · question_vector                │
      │  (dot product of unit vectors)                       │
      ▼                                                      │
 take TOP_K = 5 highest-scoring chunks                        │
      │                                                      │
      ▼                                                      ▼
 build prompt:  SYSTEM_PROMPT (rules)                              [rag.answer]
              + CONTEXT (the 5 chunks, numbered, with source)
              + last 6 turns of conversation
              + the question
      │
      ▼
 Gemini chat model  (gemini-3.6-flash, temperature 0.3)           [client.models.generate_content]
      │
      ▼
 answer text  +  a fixed one-line disclaimer  +  "Sources used" list
      │
      ▼
 rendered in the Streamlit chat UI                                [app.py]
```

Nothing is stored between sessions. Conversation history lives only in Streamlit's in-memory
`session_state` for the current browser session.

---

## 5. Technology stack — every component and why

| Layer | Technology | Version pin | Role | Why this choice / alternatives |
|---|---|---|---|---|
| Language | **Python** | 3.11+ (3.14 tested locally) | Everything | Standard for AI/ML tooling; the reference project uses it. |
| Web UI | **Streamlit** | `>=1.38,<2` | Chat interface, session state, deployment target | One Python file, no HTML/JS/CSS, free hosting on Streamlit Community Cloud. Alternatives: Flask/FastAPI + a frontend (more code), Gradio (similar). |
| LLM + embeddings | **Google Gemini** via **`google-genai`** SDK | `>=1.0,<2` | Generates answers; turns text into vectors | Free tier with no credit card; one SDK for both chat and embeddings, so dependencies stay tiny. Alternatives: OpenAI (paid), Anthropic Claude (paid), local models via Ollama (heavy download, weaker). |
| Chat model | `gemini-3.6-flash` | (configurable) | The model that writes answers | "Flash" tier = fast and free-tier friendly. Configurable via `GEMINI_CHAT_MODEL`. |
| Embedding model | `gemini-embedding-001` | (configurable) | Converts text to 768-d vectors | Google's general-purpose text embedding model, GA (generally available). |
| Vector maths | **NumPy** | `>=1.26,<3` | Stores embeddings; computes cosine similarity | The knowledge base is tiny (61 vectors), so a brute-force dot product is instant. A dedicated vector database (FAISS, Chroma, Pinecone) would be over-engineering here and add weight/complexity. |
| Config | **python-dotenv** | `>=1.0,<2` | Loads `GEMINI_API_KEY` from a local `.env` file | Keeps the secret out of code and out of git. On Streamlit Cloud the key comes from the platform's "Secrets" instead. |
| Testing | **pytest** | `>=8,<9` (dev only) | Runs the test suite | De-facto standard. Online tests auto-skip without an API key. |
| Hosting | **Streamlit Community Cloud** | — | Public HTTPS URL, deploys from GitHub | Free, zero-config, redeploys on every `git push`. |
| Source control | **Git + GitHub** | — | Version control, deploy trigger | Streamlit Cloud pulls the repo directly. |

**Dependency count is deliberately small** — four runtime packages — so cloud builds are fast
and reliable and there is less to explain or break.

---

## 6. Repository layout

```
FinancialAppChatbot/
├── app.py                       Streamlit chat UI
├── rag.py                       retrieval + LLM call; SYSTEM_PROMPT (guardrails) lives here
├── ingest.py                    builds the vector store from knowledge_base/
├── common.py                    config, Gemini client factory, embedding helper
├── list_models.py               prints the models your API key can use
│
├── knowledge_base/              the content the bot answers from (9 Markdown topics)
│   ├── glossary.md
│   ├── accounts-and-deposits.md
│   ├── loans-and-credit.md
│   ├── payments-and-transfers.md
│   ├── cards-and-credit-score.md
│   ├── investing-basics.md
│   ├── budgeting-and-saving.md
│   ├── insurance-basics.md
│   └── regulation-and-consumer-safety.md
│
├── store/                       GENERATED by ingest.py, committed so no rebuild is needed
│   ├── embeddings.npy           NumPy matrix, 61 x 768 float32
│   └── chunks.json              list of {source, topic, chunk_index, text}
│
├── tests/
│   ├── conftest.py              skips @online tests when GEMINI_API_KEY is absent
│   ├── test_offline.py          9 tests, no key/network needed
│   └── test_online.py           4 tests, need a live key
│
├── .streamlit/
│   ├── config.toml              theme
│   └── secrets.toml.example     template for the cloud secret
│
├── .env.example                 template — copy to .env and add your key
├── .gitignore                   excludes .env, .venv/, __pycache__/, .pytest_cache/
├── requirements.txt             4 runtime dependencies
├── requirements-dev.txt         adds pytest
├── pytest.ini                   registers the "online" marker
├── README.md                    quick-start and deploy guide
└── DOCUMENTATION.md             this file
```

---

## 7. File-by-file walkthrough

### `common.py` — shared configuration and helpers

- Loads `.env` with `python-dotenv`.
- Defines paths (`KB_DIR`, `STORE_DIR`, …) and tunables read from environment variables with
  sensible defaults: `CHAT_MODEL`, `EMBED_MODEL`, `EMBED_DIM` (768), `TOP_K` (5),
  `CHUNK_SIZE` (1200), `CHUNK_OVERLAP` (200).
- `get_api_key()` — reads `GEMINI_API_KEY` from the environment; if not found, tries
  `st.secrets` (that is how Streamlit Cloud supplies it); raises a clear error otherwise.
- `get_client()` — returns `google.genai.Client(api_key=...)`.
- `embed_texts(client, texts, task_type)` — calls the embedding model on a list of strings,
  then **L2-normalises** every vector (divides by its length) so that later a dot product
  equals cosine similarity. `task_type` is `RETRIEVAL_DOCUMENT` when indexing and
  `RETRIEVAL_QUERY` when embedding a question — this hint improves retrieval quality. If the
  model rejects those options, it retries with a plain call (defensive coding).

### `ingest.py` — build the vector store (run once)

- Reads every `knowledge_base/*.md`.
- `split_into_chunks(text)` — splits on blank lines into paragraphs, then **packs**
  consecutive paragraphs into chunks of up to ~1,200 characters. Oversized paragraphs are
  hard-wrapped. Each chunk after the first is prefixed with the last 200 characters of the
  previous chunk (**overlap**) so a sentence split across a boundary is not lost.
- Embeds all chunks in batches of 50 with `task_type="RETRIEVAL_DOCUMENT"`.
- Saves `store/embeddings.npy` (the matrix) and `store/chunks.json` (text + metadata).
- Current run: **9 files → 61 chunks → a 61 × 768 matrix**.

### `rag.py` — the RAG core

- `SYSTEM_PROMPT` — the instructions that define the assistant's behaviour and guardrails
  (see section 11).
- `_load_store()` — loads the `.npy` matrix and `chunks.json`; `@lru_cache` so it is read
  from disk only once per process.
- `retrieve(client, question, k)` — embeds the question (`RETRIEVAL_QUERY`), computes
  `scores = matrix @ q` (one dot product per chunk), sorts descending, returns the top `k`
  chunk records with their similarity scores.
- `_build_context(passages)` — formats the retrieved chunks as a numbered list, each labelled
  with its source file and topic.
- `answer(question, history)` — the public function. Retrieves context, assembles
  `CONTEXT + recent conversation + QUESTION`, calls
  `client.models.generate_content(model=CHAT_MODEL, contents=..., config=GenerateContentConfig(system_instruction=SYSTEM_PROMPT, temperature=0.3))`,
  appends the fixed disclaimer line, and returns `{"text": ..., "sources": [...]}`.
- Running `python rag.py "your question"` executes a one-shot query in the terminal (handy
  for testing without the UI).

### `app.py` — the Streamlit UI

- `st.set_page_config(...)` — page title, icon, layout.
- `@st.cache_resource` around a helper that imports `rag` once, so the model client and the
  vector store are not reloaded on every interaction.
- Sidebar: an "About" blurb, clickable **example questions**, and a "Clear conversation"
  button.
- Chat history is kept in `st.session_state["messages"]` (a list of role/content dicts).
- On each new question it appends the user message, calls `rag.answer(...)` with the prior
  turns as history, streams the reply into a chat bubble, and shows a **"Sources used"**
  expander listing each retrieved chunk (topic, file, index, similarity).
- Any error (missing key, API failure) is caught and shown in the chat instead of crashing.

### `list_models.py` — utility

Prints every model the current API key can access and what each supports
(`generateContent`, `embedContent`, …). Run it if a model name ever returns a 404.

### `tests/` — see section 14.

---

## 8. The knowledge base

Nine Markdown files in `knowledge_base/`, written for this project in plain language, each
ending with a "Sources consulted" list. Facts are drawn from public material published by the
RBI, SEBI, IRDAI, NPCI, the U.S. CFPB and FDIC, and the OECD. Facts are not copyrightable and
the explanatory prose is original, so the repository can be public.

| File | Covers |
|---|---|
| `glossary.md` | ~150 A–Z definitions (APR, EMI, KYC, NPA, liquidity, repo rate, VPA, yield, …) |
| `accounts-and-deposits.md` | savings vs current accounts, FD, RD, sweep-in, joint accounts, deposit insurance, fees, dormancy |
| `loans-and-credit.md` | principal/interest/EMI, the EMI formula, fixed vs floating, secured vs unsecured, loan types, the borrowing process, default |
| `payments-and-transfers.md` | NEFT, RTGS, IMPS, UPI, cheques/CTS, cards, AePS, NACH, BBPS, FASTag, SWIFT/IBAN, transfer safety |
| `cards-and-credit-score.md` | how a credit card works, billing cycle, grace period, charges, credit reports, score factors, disputes |
| `investing-basics.md` | saving vs investing, risk–return, diversification, compounding, instruments (equity, bonds, mutual funds, ETFs, gold, …), scams |
| `budgeting-and-saving.md` | building a budget, 50/30/20, zero-based, envelope, emergency fund, sinking funds, debt payoff (avalanche/snowball) |
| `insurance-basics.md` | premium/sum-assured/deductible, term vs other life, health, motor, riders, how claims work, choosing cover |
| `regulation-and-consumer-safety.md` | RBI/SEBI/IRDAI/PFRDA/NPCI, deposit vs investor protection, customer rights, complaint escalation, fraud types, what to do if defrauded |

**To extend it:** edit or add a `.md` file, run `python ingest.py`, commit
`knowledge_base/` and `store/`. The deployed app redeploys on push.

---

## 9. How retrieval works — the maths, explained simply

**Embeddings.** An embedding model maps a piece of text to a fixed-length vector (here, 768
numbers). Texts with similar meaning get vectors that point in similar directions, even if
they use different words ("home loan" and "mortgage").

**Similarity measure — cosine similarity.** For two vectors A and B:

```
cosine(A, B) = (A · B) / (|A| × |B|)
```

It is the cosine of the angle between them: `1` = same direction (very similar), `0` =
unrelated, `-1` = opposite. It ignores vector length and only compares direction, which is
what we want for meaning.

**The trick used here.** In `embed_texts` every vector is divided by its own length, so
`|A| = |B| = 1`. Then cosine similarity is just the dot product `A · B`. So for the whole
knowledge base we compute:

```
scores = embeddings_matrix  @  question_vector      # shape (61, 768) @ (768,) -> (61,)
```

one number per chunk, in a single NumPy operation. `np.argsort(-scores)[:5]` gives the five
best chunks. With 61 rows this takes well under a millisecond, so no vector database is
needed.

**Chunking.** Documents are split so that (a) each retrieved piece is small enough to fit
several into the prompt, and (b) a chunk is topically focused so its embedding is meaningful.
Overlap between chunks avoids cutting a key sentence exactly at a boundary.

---

## 10. The language-model call and prompt design

The final prompt sent to `gemini-3.6-flash` has three parts:

1. **System instruction** (`SYSTEM_PROMPT`) — role and rules (guardrails).
2. **User content**, assembled as:
   ```
   CONTEXT:
   [1] (source: payments-and-transfers.md — Payments And Transfers)
   <chunk text>
   ---
   [2] ...
   ...

   RECENT CONVERSATION:
   User: ...
   Assistant: ...

   QUESTION: <the user's question>
   ```
3. **Generation config** — `temperature = 0.3` (low, so answers stay factual and repeatable
   rather than creative).

The response text has a fixed disclaimer line appended, and the retrieved chunks are returned
alongside so the UI can show sources.

Only the **last 6 turns** of conversation are included, to keep the prompt small and cheap
while still allowing follow-up questions like "and what about IMPS?".

---

## 11. Guardrails and safety

Defined in `SYSTEM_PROMPT` in `rag.py`:

- **Stay educational.** Explain concepts, define jargon, give examples.
- **Ground in context.** If the retrieved context does not answer the question, say so and
  give only general background — do not invent specifics, numbers, or rules.
- **No personalised advice.** Do not recommend specific stocks, funds, schemes, banks, or
  products; do not tell the user what to buy/sell/do with their money. Explain principles and
  trade-offs and suggest a licensed professional.
- **Note variability.** Rules, rates, limits, and fees vary by country and change over time.
- **Scope.** Politely decline questions outside personal finance / banking.
- **Never handle credentials.** Do not ask for account numbers, card numbers, PINs, OTPs, or
  passwords; warn the user if they share them.

Additionally:

- Every answer carries the line *"Educational information only — not financial advice. Rules
  and rates vary by country and over time."*
- The UI sidebar warns users not to enter account numbers, PINs, OTPs, or passwords.
- `test_online.py::test_answer_refuses_personalised_advice` checks the refusal behaviour.

---

## 12. Running the project

**Prerequisites:** Python 3.11+, a free Gemini API key
(<https://aistudio.google.com/app/apikey>).

```bash
git clone https://github.com/aryanAyush29/FinancialAppChatbot.git
cd FinancialAppChatbot

python -m venv .venv
.venv\Scripts\Activate.ps1            # Windows PowerShell
pip install -r requirements.txt

copy .env.example .env                # then edit .env: GEMINI_API_KEY=...

python ingest.py                      # build store/ (only needed if you change the KB)
streamlit run app.py                  # open http://localhost:8501
```

**The three URLs Streamlit prints:** *Local* = this PC only (use this); *Network* = other
devices on the same Wi-Fi; *External* = a guessed public IP that almost never works (router
NAT) — use the cloud deployment to share.

**Stop:** Ctrl+C in the terminal; `deactivate` to leave the venv. There is no database or
background service.

**One-shot test without the UI:**
```bash
python rag.py "How does a fixed deposit work?"
```

---

## 13. Deployment

Streamlit Community Cloud, free, from GitHub:

1. Push the repo to GitHub. The key is **not** in the repo — `.gitignore` excludes `.env`.
   `store/embeddings.npy` and `store/chunks.json` **are** committed, so the cloud app does
   not need to rebuild the index (and does not spend embedding quota on startup).
2. <https://share.streamlit.io> → sign in with GitHub → **New app** → pick the repo, branch
   `main`, main file `app.py`, Python 3.13.
3. **Secrets** → paste `GEMINI_API_KEY = "..."`.
4. Deploy → get `https://<name>.streamlit.app`, openable from any laptop's browser.
5. Every `git push` to `main` redeploys automatically.

---

## 14. Testing strategy

`pytest`, 13 tests in `tests/`.

**Offline (9, no key or network) — `test_offline.py`:**

- chunking produces non-empty, size-bounded chunks
- chunks after the first carry an overlap prefix
- every knowledge-base file yields at least one chunk
- config values are sane (`EMBED_DIM > 0`, `TOP_K >= 1`, model names set)
- the on-disk matrix row count matches `chunks.json` and the width equals `EMBED_DIM`
- stored vectors are unit-normalised
- chunk records contain `source / topic / chunk_index / text`
- `SYSTEM_PROMPT` contains the advice-refusal and credential-safety clauses
- `_build_context` output is numbered and cites the source
- **retrieval ranking** returns the nearest row first (embeddings monkey-patched, so this
  runs offline)

**Online (4, need `GEMINI_API_KEY`) — `test_online.py`:**

- `embed_texts` returns vectors of the right shape and unit norm
- `retrieve("how is a credit score calculated?")` returns a chunk from
  `cards-and-credit-score.md`, scores sorted descending
- `answer("NEFT vs RTGS")` returns a substantial, disclaimer-tagged answer mentioning RTGS,
  with `TOP_K` sources
- `answer("which exact mutual fund should I buy?")` refuses and points to a licensed adviser

`conftest.py` auto-skips the online tests when the key is missing, so `pytest` is green in
any environment.

```bash
pip install -r requirements-dev.txt
pytest -v                     # all
pytest -m "not online"        # fast offline only
pytest -m online -v           # live end-to-end only
```

---

## 15. Cost, limits and performance

- **Cost:** the Gemini free tier covers development, testing, and a classroom demo at no
  charge. No credit card is required to obtain the key.
- **Rate limits:** the free tier limits requests per minute. Heavy simultaneous use (a whole
  class hitting one deployed instance) can cause `429`/`503` responses; the app surfaces
  these as a message rather than crashing.
- **Latency:** embedding the question is fast; the answer typically returns in ~1–4 seconds
  depending on model load. Retrieval itself is sub-millisecond.
- **Index size:** 61 chunks × 768 floats × 4 bytes ≈ 190 KB — trivially committed to git.

---

## 16. Limitations and future work

**Limitations**

- Only as knowledgeable as the 9 knowledge-base files; unknown topics get a general answer
  or a "not covered" response.
- Not real-time — it does not know today's interest rates, fees, or rule changes.
- India-leaning content; other jurisdictions are covered only briefly.
- No user accounts, no long-term memory, no analytics.
- Depends on a third-party API and its free-tier limits.

**Possible extensions**

- Expand and localise the knowledge base; ingest official PDFs directly.
- Add a WhatsApp/Telegram channel (like the original World Bank project) via a webhook.
- Swap brute-force search for FAISS/Chroma if the knowledge base grows to thousands of
  chunks.
- Add answer streaming, feedback buttons, and usage logging.
- Multilingual support (Hindi and regional languages).
- A "show the exact sentences used" highlight in the source panel.
- Evaluation harness: a fixed question set scored for retrieval hit-rate and answer quality.

---

## 17. Presentation Q&A — likely questions and answers

**Q. In one sentence, what is this?**
A web chatbot that explains banking and personal-finance concepts, using RAG so every answer
is grounded in a curated, citeable knowledge base instead of the model's memory.

**Q. What does RAG mean and why use it?**
Retrieval-Augmented Generation. Before answering, the system retrieves the most relevant
passages from our knowledge base and tells the model to answer using them. It reduces
hallucination, lets us cite sources, and lets us update knowledge by editing text files
instead of retraining.

**Q. How is this different from just using ChatGPT/Gemini directly?**
A raw model answers from training data with no sources and can invent figures. Here the facts
come from a fixed, reviewable knowledge base, the answer shows which files it used, and a
system prompt keeps it educational and stops it giving personalised advice.

**Q. Why Streamlit?**
It turns a Python script into a web chat UI with no HTML/JS, and it hosts free from GitHub,
so it can be demonstrated from any laptop's browser.

**Q. Why Google Gemini and not OpenAI?**
Gemini has a genuinely free tier with no credit card, and one SDK gives both the chat model
and the embedding model, which keeps the dependency list to four packages.

**Q. What are embeddings?**
A model that converts text into a vector of numbers (768 here) such that similar meanings
produce vectors pointing in similar directions. That lets us compare a question to knowledge
by maths.

**Q. How do you measure similarity?**
Cosine similarity — the cosine of the angle between two vectors. We normalise every vector to
length 1 at creation time, so cosine similarity becomes a plain dot product, and the whole
search is one matrix-vector multiply in NumPy.

**Q. Why no vector database (FAISS, Pinecone, Chroma)?**
The knowledge base is only 61 vectors. Brute-force comparison is sub-millisecond. A vector DB
would add a dependency and complexity for no benefit at this size. If the KB grew to
thousands of chunks, FAISS would be the drop-in upgrade.

**Q. How is the knowledge base built and is it legal to publish?**
Nine Markdown files written for this project, with facts taken from public regulator and
educational material (RBI, SEBI, IRDAI, NPCI, U.S. CFPB/FDIC, OECD). Facts are not
copyrightable and the wording is original, so the public repository is fine. Each file lists
its sources.

**Q. What is chunking and why 1,200 characters with overlap?**
Splitting documents into small passages so several fit in the prompt and each has a focused
embedding. ~1,200 characters is a few paragraphs — big enough for context, small enough to
combine. The 200-character overlap prevents a key sentence being lost exactly at a split.

**Q. What stops it giving dangerous financial advice?**
The system prompt forbids personalised investment/tax/legal advice and specific product
recommendations, requires it to defer to a licensed professional, and every answer carries a
disclaimer. There is an automated test for this refusal.

**Q. What is `temperature = 0.3`?**
A setting controlling randomness in the model's output. Low temperature makes answers more
deterministic and factual; high temperature makes them more varied/creative. We want
consistency, so it is low.

**Q. Where is the API key stored? Is it in the repo?**
No. Locally it is in a `.env` file that `.gitignore` excludes. On Streamlit Cloud it is in
the platform's encrypted "Secrets" store. The code reads it via `common.get_api_key()`.

**Q. What are the `RETRIEVAL_DOCUMENT` / `RETRIEVAL_QUERY` task types?**
A hint to the embedding model about how the text will be used. Documents and queries are
embedded slightly differently so that a short question matches a longer passage better.

**Q. How does conversation memory work?**
It is not persistent. The last six turns are kept in Streamlit's in-memory session state and
passed back into the prompt so follow-up questions work. Refreshing the page clears it.

**Q. What happens if the model name stops working?**
Google retires model versions periodically. `list_models.py` prints the currently valid
names; set `GEMINI_CHAT_MODEL` / `GEMINI_EMBED_MODEL` in `.env` (or Secrets) accordingly. We
already had to move from `gemini-2.5-flash` to `gemini-3.6-flash` during development.

**Q. What are the main failure modes?**
(1) Question outside the knowledge base → general or "not covered" answer. (2) Free-tier rate
limit → a `429/503` shown as a message. (3) Stale model name → 404 until the env var is
updated. None crash the app.

**Q. How would you evaluate answer quality properly?**
Build a fixed set of question/expected-source pairs, measure retrieval hit-rate (is the right
chunk in the top-5?), and have humans or an LLM-judge rate answer accuracy and adherence to
the guardrails. Listed under future work.

**Q. How long did the index take to build and how big is it?**
9 files → 61 chunks, embedded in two batched API calls. The stored matrix is ~190 KB.

**Q. Can it run offline?**
The retrieval maths can, but generating an answer needs the Gemini API, so a network
connection is required at query time. The offline test suite runs with no network.

**Q. How is it deployed and how do updates ship?**
Pushed to GitHub, connected to Streamlit Community Cloud, key added as a secret. Every
`git push` to `main` triggers an automatic redeploy.

---

## 18. Glossary of technical terms

| Term | Meaning in this project |
|---|---|
| **LLM** | Large Language Model — the AI that understands the question and writes the answer (Gemini here). |
| **RAG** | Retrieval-Augmented Generation — retrieve relevant text first, then let the LLM answer using it. |
| **Embedding** | A fixed-length numeric vector representing the meaning of a piece of text (768 numbers here). |
| **Vector / embedding matrix** | All chunk embeddings stacked together (61 × 768) as a NumPy array. |
| **Cosine similarity** | Measure of how aligned two vectors are; used to rank chunks against the question. |
| **Normalisation (L2)** | Scaling a vector to length 1 so cosine similarity equals a dot product. |
| **Chunk** | A small passage of a knowledge-base file (~1,200 characters) that is embedded and retrieved as a unit. |
| **Chunk overlap** | Repeating the tail of one chunk at the start of the next so boundary sentences are not lost. |
| **Top-K** | The number of highest-scoring chunks fed to the model (K = 5). |
| **Context** | The retrieved chunks inserted into the prompt for the model to answer from. |
| **System prompt / instruction** | Standing rules given to the model separately from the user's message (our guardrails). |
| **Temperature** | Randomness control for generation; 0.3 = fairly deterministic. |
| **Token** | The unit models read/generate (roughly ¾ of a word); prompts and replies are measured in tokens. |
| **task_type** | Embedding hint: `RETRIEVAL_DOCUMENT` when indexing, `RETRIEVAL_QUERY` when embedding a question. |
| **`.env` / secrets** | Where the API key is kept, outside the code and outside git. |
| **Streamlit `session_state`** | Per-browser-session in-memory store; holds the chat history. |
| **`@st.cache_resource` / `@lru_cache`** | Decorators that stop expensive objects (client, vector store) being rebuilt on every interaction. |
| **Streamlit Community Cloud** | Free hosting that runs the app from the GitHub repo and redeploys on push. |
| **FAISS / Chroma / Pinecone** | Dedicated vector-search libraries/services — not used here because the data set is tiny. |
