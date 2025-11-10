"""
Semantic embeddings storage and management for market questions.
Uses sentence-transformers for generating embeddings.
"""

import numpy as np
from typing import List, Dict, Any
from pathlib import Path
import json
from sentence_transformers import SentenceTransformer
from ..api.base import Market
from .caching import cache
from ..utils.logger import logger

class KnowledgeBase:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the knowledge base with a specified sentence transformer model.
        
        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self._model = None  # Lazy load model
        
    def _ensure_model_loaded(self):
        """Ensure the transformer model is loaded."""
        if self._model is None:
            try:
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Loaded semantic embedding model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load semantic model: {e}")
                raise
                
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single piece of text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Numpy array containing the embedding
        """
        self._ensure_model_loaded()
        return self._model.encode([text])[0]
        
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            Numpy array containing embeddings
        """
        self._ensure_model_loaded()
        return self._model.encode(texts)
        
    def update_embeddings(self, markets: List[Market]) -> None:
        """
        Update embeddings cache with new market data.
        
        Args:
            markets: List of Market objects to update embeddings for
        """
        try:
            # Load existing embeddings if any
            existing = cache.load_data("embeddings_cache.json") or {}
            
            # Convert existing embeddings from lists back to numpy arrays
            existing_embeddings = {
                k: np.array(v) for k, v in existing.items()
                if isinstance(v, list)
            }
            
            # Get questions that need new embeddings
            new_questions = [
                market.question for market in markets
                if market.market_id not in existing_embeddings
            ]
            
            if new_questions:
                logger.info(f"Generating embeddings for {len(new_questions)} new markets")
                new_embeddings = self.generate_embeddings(new_questions)
                
                # Add new embeddings
                for question, embedding in zip(new_questions, new_embeddings):
                    existing_embeddings[question] = embedding
                    
                # Save updated embeddings (convert numpy arrays to lists)
                cache_data = {
                    k: v.tolist() for k, v in existing_embeddings.items()
                }
                cache.save_data("embeddings_cache.json", cache_data)
                
        except Exception as e:
            logger.error(f"Failed to update embeddings: {e}")
            raise
            
    def find_similar_markets(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Find markets with questions similar to the query.
        
        Args:
            query: Query text to find similar markets for
            top_k: Number of similar markets to return
            
        Returns:
            List of dicts containing market info and similarity scores
        """
        try:
            # Load cached embeddings
            cached = cache.load_data("embeddings_cache.json")
            if not cached:
                return []
                
            # Convert cached embeddings back to numpy arrays
            embeddings_dict = {
                k: np.array(v) for k, v in cached.items()
                if isinstance(v, list)
            }
            
            if not embeddings_dict:
                return []
                
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Calculate similarities
            similarities = []
            for question, embedding in embeddings_dict.items():
                similarity = np.dot(query_embedding, embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(embedding)
                )
                similarities.append({
                    "question": question,
                    "similarity": float(similarity)
                })
                
            # Sort by similarity and return top-k
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Failed to find similar markets: {e}")
            return []

# Initialize global knowledge base instance
knowledge_base = KnowledgeBase()