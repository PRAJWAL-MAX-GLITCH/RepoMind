from llama_index.core.llms import LLM

from repomind.models.llm.custom.mock import FunctionCallingLLMMock
from repomind.models.llm.factories.base import LLMFactory
from repomind.models.llm.tokenizers.mock import MockTokenizer
from repomind.models.llm.tokenizers.tokenizer_base import TokenizerBase
from repomind.core.settings.settings import LLMModelConfig


class MockLLMFactory(LLMFactory):
    def _create_llm(
        self, model_config: LLMModelConfig, tokenizer: TokenizerBase | None = None
    ) -> tuple[LLM, str | None]:
        return FunctionCallingLLMMock(), "mock"

    def load_tokenizer(
        self, model_config: LLMModelConfig, raise_exception: bool = True
    ) -> TokenizerBase | None:
        """Mock using Llama Index's default tokenizer."""
        return MockTokenizer()
