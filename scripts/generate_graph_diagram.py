"""Export the current LangGraph topology as Mermaid and, optionally, PNG."""

import base64
from pathlib import Path

import requests

from app.conversations.graph import build_graph
from app.conversations.llm import LangChainModel


DIAGRAM_DIR = Path(__file__).resolve().parents[1] / "docs"


def generate_mermaid_diagram() -> str:
    graph = build_graph(model=LangChainModel(), session_factory=None, checkpointer=None)
    mermaid = graph.get_graph().draw_mermaid()
    (DIAGRAM_DIR / "langgraph_diagram.mmd").write_text(mermaid, encoding="utf-8")
    return mermaid


def generate_png_from_mermaid(mermaid: str) -> bool:
    encoded = base64.b64encode(mermaid.encode("utf-8")).decode("ascii")
    response = requests.get(f"https://mermaid.ink/img/{encoded}", params={"type": "png"}, timeout=30)
    if not response.ok or not response.content.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    (DIAGRAM_DIR / "langgraph_diagram.png").write_bytes(response.content)
    return True


def main() -> None:
    mermaid = generate_mermaid_diagram()
    print("Diagrama Mermaid salvo em docs/langgraph_diagram.mmd")
    try:
        if generate_png_from_mermaid(mermaid):
            print("PNG salvo em docs/langgraph_diagram.png")
        else:
            print("Não foi possível gerar o PNG; use o arquivo Mermaid.")
    except requests.RequestException as exc:
        print(f"Não foi possível acessar mermaid.ink: {type(exc).__name__}")


if __name__ == "__main__":
    main()
