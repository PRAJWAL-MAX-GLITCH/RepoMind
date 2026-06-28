import logging
from repomind.core.di import get_global_injector
from repomind.models.llm.llm_component import LLMComponent
from repomind.rag.retriever import RepositoryRetriever

logger = logging.getLogger(__name__)

def query_repo(question: str, repo_name: str) -> str:
    """
    Answers a developer's question about a specific repository.
    
    Args:
        question (str): The semantic question.
        repo_name (str): The name of the repository.
        
    Returns:
        str: The generated answer.
    """
    logger.info("Executing query on repo '%s': %s", repo_name, question)
    
    # 1. Retrieve context
    retriever = RepositoryRetriever()
    chunks = retriever.retrieve(query=question, repo_name=repo_name, top_k=5)
    
    if not chunks:
        return f"No context found in repository '{repo_name}' to answer the question."
        
    # 2. Build context blocks
    context_blocks = []
    for idx, chunk in enumerate(chunks, 1):
        file_path = chunk.get("file_path", "Unknown File")
        start_line = chunk.get("start_line", "?")
        end_line = chunk.get("end_line", "?")
        content = chunk.get("content", "")
        
        block = f"--- Context {idx} ---\nFile: {file_path} (Lines {start_line}-{end_line})\n\n{content}\n"
        context_blocks.append(block)
        
    context_str = "\n".join(context_blocks)
    
    # 3. Prompt building
    system_prompt = (
        "You are RepoMind, an expert senior developer AI. "
        "Answer the user's question about the codebase concisely, like a senior engineer doing a code review. "
        "Avoid generic LLM fluff or overly conversational language. "
        "CRITICAL: When referencing code, you MUST explicitly cite the exact file path and line range provided in the context (e.g., `src/main.py:10-25`). "
        "Only use the provided context. If it's insufficient, state exactly what is missing."
    )
    
    full_prompt = f"{system_prompt}\n\nCode Context:\n{context_str}\n\nQuestion: {question}\nAnswer:"
    
    # 4. LLM Generation
    llm_component = get_global_injector().get(LLMComponent)
    llm = llm_component.get_llm()
    
    logger.info("Sending prompt to LLM...")
    response = llm.complete(full_prompt)
    
    return str(response)
