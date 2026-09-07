# 💰 FinLit Assistant — a RAG chatbot for financial literacy

A question-answering chatbot that explains **banking terms, loans, credit cards, payments,
budgeting, insurance and investing basics**. It uses **Retrieval-Augmented Generation
(RAG)**: every answer is grounded in a curated knowledge base of financial-literacy notes,
so responses stay accurate and consistent instead of being made up.

Inspired by the [World Bank WhatsApp-RAG-Example](https://github.com/worldbank/WhatsApp-RAG-Example),
rebuilt as a lightweight **Streamlit** app that deploys free from GitHub.

> ⚠️ Educational information only. This project does **not** give personalised financial,
> investment, tax or legal advice.

---

## How it works

```
knowledge_base/*.md ──► ingest.py ──► store/embeddings.npy + store/chunks.json
                                              │
 user question ─► embed ─► cosine similarity ─┤ (top-K relevant chunks)
                                              ▼
                        Gemini chat model + system rules ─► grounded answer + sources
```

| Component | Choice | Why |
|---|---|---|
| UI | Streamlit | One file, runs anywhere, free hosting |
| LLM + embeddings | Google Gemini (free tier) | No credit card; light dependency |
| Vector search | NumPy cosine similarity | KB is small; no heavy vector DB needed |
| Knowledge base | Hand-written Markdown in `knowledge_base/` | Easy to read, edit and extend |

### Project layout

```
app.py                 Streamlit chat UI
rag.py                 retrieve context + call Gemini (system prompt / guardrails here)
ingest.py              build the vector store from knowledge_base/
common.py              config + Gemini client + embedding helper
list_models.py         prints models your API key can use (run if a model name errors)
knowledge_base/        the content the bot answers from (9 Markdown topics)
store/                 generated: embeddings.npy + chunks.json (commit these)
requirements.txt       Python dependencies
.env.example           template for your API key + optional settings
```

---

## 1. Prerequisites

- **Python 3.11+** (3.14 works locally; **Streamlit Cloud currently maxes at 3.13**, so
  pick 3.13 in the deploy dialog). Check with `python --version`.
- A free **Gemini API key**: <https://aistudio.google.com/app/apikey> (Google account only,
  no card).

## 2. Local setup

```bash
git clone <your-repo-url>
cd CHATBOT

python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt

cp .env.example .env        # Windows: copy .env.example .env
# then edit .env and paste your key into GEMINI_API_KEY
```

## 3. Build the knowledge index (once)

```bash
python ingest.py
```

This creates `store/embeddings.npy` and `store/chunks.json`. Re-run it any time you edit
files in `knowledge_base/`. **Commit the `store/` files** so the deployed app and other
laptops don't need to rebuild.

Quick sanity check without the UI:

```bash
python rag.py "What is the difference between a debit and a credit card?"
```

## 4. Run the app

```bash
streamlit run app.py
```

Opens at <http://localhost:8501>.

---

## 5. Running the tests

```bash
pip install -r requirements-dev.txt
pytest -v
```

- **Offline tests** (chunking, config, the on-disk vector store, prompt guardrails,
  retrieval ranking with embeddings mocked) run with no API key.
- **Online tests** (`@pytest.mark.online`: real embeddings, retrieval relevance, a full
  `answer()` round-trip, and an advice-refusal check) run only when `GEMINI_API_KEY` is
  set; otherwise pytest skips them automatically.

```bash
pytest -m online -v        # only the live end-to-end tests
pytest -m "not online" -v  # only the fast offline tests
```

Other quick manual checks:

```bash
python -m py_compile *.py            # syntax
python list_models.py               # verify the key + see valid model names
python rag.py "How does an FD work?" # one-shot end-to-end query in the terminal
```

## 6. Deploy free to Streamlit Community Cloud (for presenting from any laptop)

1. Push this project to **GitHub** (public is fine — the key lives only in `.env`, which is
   git-ignored):
   ```bash
   git init
   git add .
   git commit -m "FinLit Assistant: RAG financial-literacy chatbot"
   git branch -M main
   git remote add origin https://github.com/aryanAyush29/FinancialAppChatbot.git
   git push -u origin main
   ```
   After the first public push, **regenerate your Gemini key** at
   <https://aistudio.google.com/app/apikey> and update `.env` + the Streamlit secret.
2. Go to <https://share.streamlit.io> → sign in with GitHub → **New app**.
3. Pick the repo, branch `main`, main file `app.py`. Under **Advanced settings** choose
   **Python 3.13**.
4. Open **Secrets** and paste:
   ```toml
   GEMINI_API_KEY = "your_real_key"
   ```
5. **Deploy**. You get a public URL like `https://<name>.streamlit.app` — open it in any
   browser, on any laptop, during your presentation. No install needed.

If Wi-Fi fails on the day, the local fallback is just steps 2–4 above on the spare laptop.

---

## Configuration (optional)

Set these in `.env` (local) or Secrets (cloud). Defaults are sensible.

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | **required** |
| `GEMINI_CHAT_MODEL` | `gemini-2.5-flash` | Chat model. If it errors ("model not found"), run `python list_models.py` and set a current name. |
| `GEMINI_EMBED_MODEL` | `gemini-embedding-001` | Embedding model. Must be the **same** for `ingest.py` and the app. |
| `EMBED_DIM` | `768` | Embedding size. Change → re-run `ingest.py`. |
| `RAG_TOP_K` | `5` | How many chunks to feed the model. |

> Model names change over time. If you see "model not found", check
> <https://ai.google.dev/gemini-api/docs/models>, run `python list_models.py`, and update
> `.env`, then re-run `python ingest.py` if you changed the embedding model.

---

## Extending the knowledge base

1. Add or edit a `.md` file in `knowledge_base/` (plain prose; blank lines separate
   chunks).
2. `python ingest.py`
3. `git add knowledge_base store && git commit -m "Expand KB" && git push`

The Streamlit Cloud app redeploys automatically on push.

---

## Guardrails

Defined in `SYSTEM_PROMPT` in [`rag.py`](rag.py): explain concepts, stay grounded in
retrieved context, refuse personalised advice and specific product recommendations, flag
that rules/rates vary, and never handle credentials. Every answer carries a disclaimer
line.

## Limitations

- Only as good as the knowledge base — currently ~9 topics with an India lean.
- Not real-time: it does not know today's interest rates, fees or regulations.
- The free Gemini tier has rate limits; heavy simultaneous use during a demo may throttle.

## Credits

Concept adapted from the World Bank
[WhatsApp-RAG-Example](https://github.com/worldbank/WhatsApp-RAG-Example).
Knowledge-base facts drawn from public material by the RBI, SEBI, IRDAI, NPCI, the U.S. CFPB
and FDIC, and the OECD; explanatory text written for this project.
