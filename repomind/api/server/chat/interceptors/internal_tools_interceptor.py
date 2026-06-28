from injector import inject, singleton

from repomind.rag.context.models.context_layer import (
    ToolDefinitionsLayer,
)
from repomind.rag.context.models.layer_type import LayerType
from repomind.rag.engines.chat_loop.interceptors.chat_loop_interceptor import (
    ChatRequestLoopInterceptor,
)
from repomind.rag.engines.chat_loop.models.chat_loop_interceptor_context import (
    ChatLoopInterceptorContext,
)
from repomind.rag.engines.chat_loop.models.chat_loop_phase import (
    InterceptorPhase,
)
from repomind.rag.engines.chat_loop.utils.request_builder import (
    build_request_from_context_stack,
)
from repomind.rag.prompts.prompt_builder import PromptBuilderService
from repomind.components.tools.tool_pipeline import ToolPipeline


@singleton
class InternalToolRequestInterceptor(ChatRequestLoopInterceptor):
    @inject
    def __init__(
        self,
        tool_pipeline: ToolPipeline,
        prompt_builder: PromptBuilderService,
    ) -> None:
        self._tool_pipeline = tool_pipeline
        self._prompt_builder = prompt_builder

    async def intercept(self, context: ChatLoopInterceptorContext) -> None:
        if (
            context.phase != InterceptorPhase.VALIDATION
            and context.phase != InterceptorPhase.BEFORE_ITERATION
        ):
            return

        state = context.state
        stack = state.input.context_stack

        tool_request = build_request_from_context_stack(state.input.request, stack)
        final_tool_request = await self._tool_pipeline.contextualize_internal_tools(
            tool_request
        )
        tools = final_tool_request.tool_config.tools

        if context.phase == InterceptorPhase.BEFORE_ITERATION and tools:
            tools = self._prompt_builder.seed_tool_instructions(tools)

        stack = state.input.context_stack
        stack = stack.remove_layers_of_type(LayerType.TOOL_DEFINITIONS)
        if tools:
            stack = stack.append_layer(
                ToolDefinitionsLayer(tools=tools, source="internal_tools")
            )
        state.input.context_stack = stack
        context.set_state(state)
