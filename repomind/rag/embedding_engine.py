from typing import List
from repomind.core.di import get_global_injector
from repomind.models.embedding.embedding_component import EmbeddingComponent

class EmbeddingEngine:
    """
    Wraps existing embedding models to vector-ize code chunks and queries.
    """
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name
        # Get active EmbeddingComponent via injector
        self.embedding_component = get_global_injector().get(EmbeddingComponent)
        self.embed_model = self.embedding_component.get_embed(model_id=self.model_name)

    def embed_text(self, text: str) -> List[float]:
        """
        Generates an embedding vector for a given text.
        
        Args:
            text (str): The text to embed.
            
        Returns:
            List[float]: The generated embedding vector.
        """
        return self.embed_model.get_text_embedding(text)

