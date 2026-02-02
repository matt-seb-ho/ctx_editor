from azure.identity import (
    AzureCliCredential,
    get_bearer_token_provider,
)
from openai import AsyncAzureOpenAI

AZURE_ENDPOINT = "https://fxdata-eastus2.openai.azure.com"
API_VERSION = "2024-10-21"


def setup_azure_oai_client():
    token_provider = get_bearer_token_provider(
        AzureCliCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    client = AsyncAzureOpenAI(
        azure_endpoint=AZURE_ENDPOINT,
        azure_ad_token_provider=token_provider,
        api_version=API_VERSION,
    )
    return client
