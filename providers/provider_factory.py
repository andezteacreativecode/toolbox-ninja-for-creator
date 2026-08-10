from providers.base_provider import BaseAIProvider
from providers.ollama_provider import OllamaProvider
from providers.openrouter_provider import OpenRouter9RouterProvider

class ProviderFactory:
    @staticmethod
    def get_provider(provider_type: str, config: dict) -> BaseAIProvider:
        provider_type = provider_type.lower()
        if provider_type == "ollama":
            return OllamaProvider(config)
        elif provider_type in ("9router", "openrouter"):
            return OpenRouter9RouterProvider(config)
        else:
            raise ValueError(f"Provider '{provider_type}' tidak dikenal.")
