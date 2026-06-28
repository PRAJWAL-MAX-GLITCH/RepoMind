from llama_index.core.llms import LLM

from repomind.models.llm.factories.base import LLMFactory
from repomind.models.llm.tokenizers.tokenizer_base import TokenizerBase
from repomind.core.settings.settings import LLMModelConfig


class OpenAILLMFactory(LLMFactory):
    """Main OpenAI factory.

    Routes to the Responses API factory when ``model_config.api_type == "responses"``,
    otherwise delegates to the Chat Completions factory.
    """

    def _create_llm(
        self, model_config: LLMModelConfig, tokenizer: TokenizerBase | None = None
    ) -> tuple[LLM, str | None]:
        if model_config.api_type == "responses":
            from repomind.models.llm.factories.responses.generic import (
                OpenAIGenericResponsesFactory,
            )

            return OpenAIGenericResponsesFactory(self.settings)._create_llm(
                model_config,
                tokenizer=tokenizer,
            )

        from repomind.models.llm.factories.completions.generic import (
            OpenAIGenericCompletionsFactory,
        )

        return OpenAIGenericCompletionsFactory(self.settings)._create_llm(
            model_config,
            tokenizer=tokenizer,
        )
