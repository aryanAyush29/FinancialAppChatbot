"""Streamlit chat UI for the financial-literacy RAG chatbot."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="FinLit Assistant", page_icon="💰", layout="centered")

EXAMPLES = [
    "What is a credit score and how is it calculated?",
    "Difference between NEFT, RTGS, IMPS and UPI?",
    "How does a fixed deposit work?",
    "What is compound interest? Give a simple example.",
    "Secured vs unsecured loan — what's the difference?",
    "How can I recognise a UPI or KYC scam?",
]


@st.cache_resource(show_spinner=False)
def _rag():
    import rag

    return rag


def main() -> None:
    st.title("💰 FinLit Assistant")
    st.caption(
        "Ask about banking terms, loans, cards, payments, budgeting, insurance and "
        "investing basics. Educational only — not financial advice."
    )

    with st.sidebar:
        st.header("About")
        st.write(
            "A retrieval-augmented chatbot that answers from a curated financial-literacy "
            "knowledge base, so answers stay grounded and consistent."
        )
        st.subheader("Try an example")
        for ex in EXAMPLES:
            if st.button(ex, use_container_width=True):
                st.session_state["pending"] = ex
        st.divider()
        if st.button("🗑️ Clear conversation", use_container_width=True):
            st.session_state["messages"] = []
            st.rerun()
        st.caption("Built with Streamlit + Google Gemini. Do not share account numbers, "
                   "PINs, OTPs or passwords here.")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("Sources used"):
                    for s in msg["sources"]:
                        st.markdown(
                            f"- **{s['topic']}** (`{s['source']}`, chunk {s['chunk_index']}, "
                            f"similarity {s['score']:.2f})"
                        )

    prompt = st.chat_input("Ask a financial-literacy question…")
    if not prompt and st.session_state.get("pending"):
        prompt = st.session_state.pop("pending")

    if not prompt:
        return

    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state["messages"][:-1]
                ]
                result = _rag().answer(prompt, history=history)
                text, sources = result["text"], result["sources"]
            except Exception as e:  # noqa: BLE001 — surface any setup/API error to the user
                text, sources = f"⚠️ {e}", []
        st.markdown(text)
        if sources:
            with st.expander("Sources used"):
                for s in sources:
                    st.markdown(
                        f"- **{s['topic']}** (`{s['source']}`, chunk {s['chunk_index']}, "
                        f"similarity {s['score']:.2f})"
                    )

    st.session_state["messages"].append(
        {"role": "assistant", "content": text, "sources": sources}
    )


if __name__ == "__main__":
    main()
