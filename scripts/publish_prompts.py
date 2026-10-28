"""Publish the four initial Langfuse prompts when explicitly invoked.

Preview: python -m scripts.publish_prompts
Publish: python -m scripts.publish_prompts --publish
"""

import argparse

from app import config
from app.conversations.prompts import LOCAL_PROMPTS


def main() -> None:
    parser = argparse.ArgumentParser(description="Publicar prompts iniciais do medAgenda no Langfuse")
    parser.add_argument("--publish", action="store_true", help="Criar versões com o rótulo production")
    args = parser.parse_args()

    if not args.publish:
        print("Prévia: " + ", ".join(LOCAL_PROMPTS))
        print("Use --publish para criar versões production no projeto Langfuse configurado.")
        return
    if not (config.LANGFUSE_PUBLIC_KEY and config.LANGFUSE_SECRET_KEY):
        parser.error("Configure LANGFUSE_PUBLIC_KEY e LANGFUSE_SECRET_KEY antes de publicar.")

    from langfuse import Langfuse

    client = Langfuse(
        public_key=config.LANGFUSE_PUBLIC_KEY,
        secret_key=config.LANGFUSE_SECRET_KEY,
        base_url=config.LANGFUSE_BASE_URL,
    )
    for name, template in LOCAL_PROMPTS.items():
        prompt = client.create_prompt(
            name=name, prompt=template, type="text", labels=["production"],
            commit_message="Versão inicial do prompt do medAgenda",
        )
        print(f"{name}: version {prompt.version} (production)")


if __name__ == "__main__":
    main()
