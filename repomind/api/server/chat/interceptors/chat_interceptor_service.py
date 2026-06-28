from injector import inject, singleton

from repomind.rag.engines.chat_loop.interceptors.chat_loop_interceptor_chain import (
    ChatLoopInterceptorChain,
)
from repomind.rag.engines.chat_loop.interceptors.restore_stateless_input_interceptor import (
    RestoreStatelessInputInterceptorRequest,
)
from repomind.rag.prompts.prompt_builder import PromptBuilderService
from repomind.api.server.chat.interceptors.citation_interceptor import (
    CitationRequestInterceptor,
)
from repomind.api.server.chat.interceptors.condensation_interceptor import (
    CondensationRequestInterceptor,
)
from repomind.api.server.chat.interceptors.configure_tool_interceptor import (
    ConfigureToolRequestInterceptor,
)
from repomind.api.server.chat.interceptors.default_values_interceptor import (
    DefaultValuesRequestInterceptor,
)
from repomind.api.server.chat.interceptors.document_processing_interceptor import (
    DocumentProcessingRequestInterceptor,
)
from repomind.api.server.chat.interceptors.extract_citation_interceptor import (
    ExtractCitationInterceptor,
)
from repomind.api.server.chat.interceptors.filter_event_by_type_interceptor import (
    FilterZylonInterceptor,
)
from repomind.api.server.chat.interceptors.internal_tools_interceptor import (
    InternalToolRequestInterceptor,
)
from repomind.api.server.chat.interceptors.mcp_interceptor import McpRequestInterceptor
from repomind.api.server.chat.interceptors.multimodal_interceptor import (
    MultimodalRequestInterceptor,
)
from repomind.api.server.chat.interceptors.ping_loop_interceptor import PingInterceptor
from repomind.api.server.chat.interceptors.platform_guidelines_interceptor import (
    PlatformGuidelinesInterceptor,
)
from repomind.api.server.chat.interceptors.skill_tool_visibility_interceptor import (
    SkillToolVisibilityInterceptor,
)
from repomind.api.server.chat.interceptors.skills_loop_interceptor import (
    SkillsInterceptor,
)
from repomind.api.server.chat.interceptors.skills_validation_interceptor import (
    SkillsValidationInterceptor,
)
from repomind.api.server.chat.interceptors.system_prompt_interceptor import (
    SystemPromptRequestInterceptor,
)
from repomind.api.server.chat.interceptors.tool_choice_interceptor import (
    ToolChoiceRequestInterceptor,
)
from repomind.api.server.chat.interceptors.validator_request_interceptor import (
    ValidatorRequestInterceptor,
)
from repomind.core.settings.settings import Settings


@singleton
class ChatInterceptorService:
    """Builds and owns the interceptor chain template.

    Call :meth:`get_chain` to obtain an independent clone of the chain for
    each request — the interceptor instances are shared (they must be
    stateless) while the chain state is deep-copied so concurrent requests
    never interfere with each other.
    """

    @inject
    def __init__(
        self,
        settings: Settings,
        prompt_builder_service: PromptBuilderService,
        # --- request interceptors (run once, order matters) ---
        validation_request_interceptor: ValidatorRequestInterceptor,
        default_values_interceptor: DefaultValuesRequestInterceptor,
        mcp_interceptor: McpRequestInterceptor,
        skills_validation_interceptor: SkillsValidationInterceptor,
        skills_interceptor: SkillsInterceptor,
        internal_tools_interceptor: InternalToolRequestInterceptor,
        skill_tool_visibility_interceptor: SkillToolVisibilityInterceptor,
        tool_choice_interceptor: ToolChoiceRequestInterceptor,
        configure_tool_interceptor: ConfigureToolRequestInterceptor,
        # --- loop interceptors (run each iteration, order matters) ---
        multimodal_interceptor: MultimodalRequestInterceptor,
        citation_interceptor: CitationRequestInterceptor,
        platform_guidelines_interceptor: PlatformGuidelinesInterceptor,
        condensation_interceptor: CondensationRequestInterceptor,
        # --- response interceptors (run each iteration, order matters) ---
        extract_citation_response_interceptor: ExtractCitationInterceptor,
        filter_event_by_type_interceptor: FilterZylonInterceptor,
        ping_interceptor: PingInterceptor,
    ) -> None:
        self._prompt_builder_service = prompt_builder_service

        self._chain: ChatLoopInterceptorChain = (
            ChatLoopInterceptorChain()
            # Init interceptors
            .add_range(
                "init",
                requests=[validation_request_interceptor, default_values_interceptor],
            )
            # Init tools, internal tools & platform skills
            .add_range(
                "tools",
                requests=[
                    mcp_interceptor,
                    skills_validation_interceptor,
                    skills_interceptor,
                    internal_tools_interceptor,
                    platform_guidelines_interceptor,
                    skill_tool_visibility_interceptor,
                    tool_choice_interceptor,
                    configure_tool_interceptor,
                ],
            )
            # Preprocess the chat history
            .add_range(
                "preprocess",
                requests=[multimodal_interceptor],
            )
            # Configure citations and documents
            .add_range(
                "document",
                requests=[
                    citation_interceptor,
                    DocumentProcessingRequestInterceptor(
                        add_context_to_system_prompt=False,
                    ),
                    platform_guidelines_interceptor,
                ],
            )
            # Calculate the prompt
            .add_range(
                "prompt",
                requests=[
                    SystemPromptRequestInterceptor(
                        prompt_builder_service=prompt_builder_service,
                        add_context_to_system_prompt=False,
                    )
                ],
            )
            # Add memory interceptor
            .add_range("memory", requests=[condensation_interceptor])
            # If the normal behavior is added to the system, we have
            # to recalculate the documents and prompt after condensation
            .add_range(
                "recalculate",
                requests=[
                    RestoreStatelessInputInterceptorRequest(
                        reset_user_instructions=True,
                        reset_runtime_instructions=True,
                        reset_documents=False,
                        reset_tools=False,
                    ),
                    citation_interceptor,
                    DocumentProcessingRequestInterceptor(
                        add_context_to_system_prompt=True
                    ),
                    SystemPromptRequestInterceptor(
                        prompt_builder_service=prompt_builder_service,
                        add_context_to_system_prompt=True,
                    ),
                ],
                condition=settings.chat.add_context_to_system_prompt,
            )
            # --- Response ---
            # Extract citations if they are enabled
            .add_range(
                "document",
                responses=[
                    extract_citation_response_interceptor,
                ],
            )
            # Guarantee a valid response
            .add_range(
                "sanity",
                responses=[
                    filter_event_by_type_interceptor,
                    ping_interceptor,
                ],
            )
        )

    def get_chain(self) -> ChatLoopInterceptorChain:
        """Return an independent clone of the interceptor chain.

        Each call produces a fresh clone whose state is isolated from all
        other clones, while the underlying interceptor instances are shared.
        """
        return self._chain.clone()
