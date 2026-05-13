"""Smoke test for non-OpenAI models on Michel's mgalley-foundry2 Azure AI Foundry endpoint.

Combines:
  - The endpoint + OpenAI-client pattern from Michel's instructions
    (`/home/v-homatthew/misc/michel_non_oai_instr.md`)
  - The managed-identity auth pattern from `/home/v-homatthew/misc/test_trapi.py`
    (chained AzureCliCredential -> ManagedIdentityCredential)

Usage:
    python scripts/test_non_oai.py
    python scripts/test_non_oai.py --model DeepSeek-V3.2
    python scripts/test_non_oai.py --model grok-4-1-fast-non-reasoning --prompt "Hi there"
"""

import argparse

from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    ManagedIdentityCredential,
)
from openai import OpenAI

ENDPOINT = "https://mgalley-foundry2.services.ai.azure.com/openai/v1/"

# Cognitive Services / AI Services AAD scope.
SCOPE = "https://cognitiveservices.azure.com/.default"

KNOWN_MODELS = [
    "DeepSeek-V3.2",
    "DeepSeek-V3.1",
    "DeepSeek-V3.2-Speciale",
    "DeepSeek-V4-Flash",
    "DeepSeek-R1-0528",
    "grok-4-1-fast-non-reasoning",
    "grok-4-1-fast-reasoning",
    "grok-4-20-non-reasoning",
    "grok-4-20-reasoning",
    "Kimi-K2.6",
    "Llama-3.3-70B-Instruct",
    "Phi-4",
    "Phi-4-reasoning",
    "Mistral-Large-3",
]


def get_bearer_token(scope: str = SCOPE) -> str:
    credential = ChainedTokenCredential(
        AzureCliCredential(),
        ManagedIdentityCredential(),
    )
    return credential.get_token(scope).token


def build_client() -> OpenAI:
    token = get_bearer_token()
    return OpenAI(base_url=ENDPOINT, api_key=token)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model",
        default="DeepSeek-V3.2",
        help=f"Deployment name. Known: {', '.join(KNOWN_MODELS)}",
    )
    parser.add_argument(
        "--prompt",
        default="What is the capital of France? Answer in one word.",
    )
    args = parser.parse_args()

    client = build_client()
    completion = client.chat.completions.create(
        model=args.model,
        messages=[{"role": "user", "content": args.prompt}],
    )
    msg = completion.choices[0].message
    print(f"=== model: {args.model} ===")
    print(f"content: {msg.content}")
    if getattr(msg, "reasoning_content", None):
        print(f"reasoning: {msg.reasoning_content}")


if __name__ == "__main__":
    main()
