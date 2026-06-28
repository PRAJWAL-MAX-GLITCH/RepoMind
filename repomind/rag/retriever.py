from typing import List, Dict, Any
from llama_index.core.vector_stores.types import (
    VectorStoreQuery,
    MetadataFilters,
    MetadataFilter,
    FilterCondition,
)
from repomind.core.di import get_global_injector
from repomind.vector_store.vector_store.vector_store_component import VectorStoreComponent
from repomind.rag.embedding_engine import EmbeddingEngine

class RepositoryRetriever:
    """
    Executes vector similarity searches against the indexed codebase,
    filtered by repository name.
    """
    def __init__(self, vector_store=None):
        self.vector_store_component = get_global_injector().get(VectorStoreComponent)
        self.vector_store = vector_store or self.vector_store_component.vector_store(
            self.vector_store_component.default_collection
        )
        self.embedding_engine = EmbeddingEngine()

    def retrieve(self, query: str, repo_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves the most semantically similar code chunks for a given query in a specific repository.
        
        Args:
            query (str): The search question.
            repo_name (str): The repository name to filter by.
            top_k (int): Number of top results to return.
            
        Returns:
            List[Dict[str, Any]]: The matched code chunks and their metadata.
        """
        # Embed the query
        query_embedding = self.embedding_engine.embed_text(query)

        # Build metadata filters for the specific repository
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key="repo_name", value=repo_name)
            ],
            condition=FilterCondition.AND
        )

        # Create query
        vector_query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=top_k,
            filters=filters
        )

        # Execute query
        result = self.vector_store.query(vector_query)

        # Format results
        chunks = []
        if result.nodes:
            for node in result.nodes:
                chunk_data = node.metadata.copy()
                chunk_data["content"] = node.get_content()
                chunks.append(chunk_data)

        return chunks
