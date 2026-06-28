from typing import List
from llama_index.core.schema import TextNode
from repomind.core.di import get_global_injector
from repomind.vector_store.vector_store.vector_store_component import VectorStoreComponent
from repomind.models.chunk_schema import ChunkMetadata

class Indexer:
    """
    Interfaces with the vector store to insert chunked data.
    """
    def __init__(self, vector_store=None):
        self.vector_store_component = get_global_injector().get(VectorStoreComponent)
        self.vector_store = vector_store or self.vector_store_component.vector_store(
            self.vector_store_component.default_collection
        )

    def index_chunks(self, chunks: List[ChunkMetadata], embeddings: List[List[float]]) -> None:
        """
        Takes processed code chunks and persists them in the vector store.
        
        Args:
            chunks (List[ChunkMetadata]): A list of ChunkMetadata objects.
            embeddings (List[List[float]]): Corresponding embedding vectors.
        """
        nodes = []
        for chunk, embedding in zip(chunks, embeddings):
            # Qdrant client builder / patched qdrant store expects nodes of type BaseNode (e.g. TextNode)
            # metadata fields are mapped onto the point payload.
            # We map ChunkMetadata's model fields onto the node's metadata dict.
            metadata = chunk.model_dump(exclude={"content"})
            node = TextNode(
                text=chunk.content,
                id_=chunk.chunk_id,
                embedding=embedding,
                metadata=metadata,
            )
            nodes.append(node)

        if nodes:
            self.vector_store.add(nodes)

