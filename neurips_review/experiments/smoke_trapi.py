"""TRAPI smoke test: find a working (instance, credential) combo for gpt-5.4-mini.

Tries redmond/interactive (unpinned + subscription-pinned) and gcr/shared.
Prints which combos return a completion. Uses the OpenAI-v1 path
(base_url=.../{instance}/openai/v1) with the AAD token as api_key, mirroring
~/misc/trapi_example.py and the repo's azure_foundry client path.
"""
import sys
from openai import OpenAI
from azure.identity import AzureCliCredential, get_bearer_token_provider

SCOPE = "api://trapi/.default"
HOST = "https://trapi.research.microsoft.com"
MODEL = "gpt-5.4-mini_2026-03-17"
REDMOND_SUB = "39675fbf-5b47-472e-9bb9-5570c6edbd4f"

combos = [
    ("redmond/interactive", None),
    ("redmond/interactive", REDMOND_SUB),
    ("gcr/shared", None),
]

for instance, sub in combos:
    label = f"{instance} (sub={sub or 'active'})"
    try:
        cred = AzureCliCredential(subscription=sub) if sub else AzureCliCredential()
        tp = get_bearer_token_provider(cred, SCOPE)
        client = OpenAI(base_url=f"{HOST}/{instance}/openai/v1", api_key=tp)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Reply with one word: ping"}],
        )
        print(f"OK   {label}: {resp.choices[0].message.content!r}")
    except Exception as e:
        msg = str(e).replace("\n", " ")[:180]
        print(f"FAIL {label}: {type(e).__name__}: {msg}")
