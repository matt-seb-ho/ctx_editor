from azure.identity import (
    AzureCliCredential,
    get_bearer_token_provider,
)
from openai import AsyncOpenAI

AZURE_ENDPOINT = "https://fxdata-eastus2.openai.azure.com/openai/v1"


def setup_azure_oai_client():
    token_provider = get_bearer_token_provider(
        AzureCliCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    client = AsyncOpenAI(
        base_url=AZURE_ENDPOINT,
        api_key=token_provider,
    )
    return client
