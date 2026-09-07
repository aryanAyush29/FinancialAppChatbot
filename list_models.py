"""Print the Gemini models your API key can use.

Run this if you hit a "model not found" error, then set the correct names in .env
(GEMINI_CHAT_MODEL / GEMINI_EMBED_MODEL).

    python list_models.py
"""
from common import get_client


def main() -> None:
    client = get_client()
    print("Models available to your key:\n")
    for m in client.models.list():
        actions = getattr(m, "supported_actions", None) or getattr(
            m, "supported_generation_methods", []
        )
        print(f"  {m.name:45s}  {', '.join(actions)}")


if __name__ == "__main__":
    main()
