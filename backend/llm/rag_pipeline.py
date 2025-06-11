"""
RAG (Retrieval-Augmented Generation) pipeline
Combines document retrieval with Ollama LLM for contextual responses
"""
import logging
from typing import List, Dict, Optional, Tuple
import time
from dataclasses import dataclass

from llm.ollama_client import OllamaClient, OllamaConfig
from embeddings.store import VectorStore
from embeddings.embedder import EmbeddingModel

logger = logging.getLogger(__name__)

@dataclass
class RAGResult:
    """Result from RAG pipeline"""
    response: str
    sources: List[Dict]
    context_used: str
    response_time_ms: float
    retrieval_count: int

class RAGPipeline:
    """
    RAG pipeline that retrieves relevant documents and generates contextual responses
    """
    
    def __init__(self, 
                 ollama_base_url: str = "http://localhost:11434",
                 model_name: str = "llama3.2",
                 vector_store_path: str = "data/corpus.db"):
        """
        Initialize RAG pipeline
        
        Args:
            ollama_base_url: Ollama API URL
            model_name: Ollama model to use
            vector_store_path: Path to vector database
        """
        self.config = OllamaConfig()
        self.config.base_url = ollama_base_url
        self.config.default_model = model_name
        
        # Initialize components
        self.ollama = OllamaClient(ollama_base_url, model_name)
        self.vector_store = VectorStore(db_path=vector_store_path)
        self.embedder = EmbeddingModel()
        
        logger.info("RAG Pipeline initialized")
    
    def query(self, 
              user_query: str,
              chat_history: Optional[List[Dict]] = None,
              max_sources: int = 5,
              similarity_threshold: float = 0.5,
              use_context: bool = True) -> RAGResult:
        """
        Process a query through the RAG pipeline
        
        Args:
            user_query: User's question
            chat_history: Previous conversation messages
            max_sources: Maximum number of source documents to retrieve
            similarity_threshold: Minimum similarity for document retrieval
            use_context: Whether to use retrieved context for generation
            
        Returns:
            RAGResult with response and metadata
        """
        start_time = time.time()
        
        try:
            # Step 1: Retrieve relevant documents
            sources = []
            context_text = ""
            
            if use_context and self.vector_store.get_chunk_count() > 0:
                logger.info(f"Retrieving context for query: '{user_query[:50]}...'")
                
                # Generate query embedding
                query_embedding = self.embedder.embed_query(user_query)
                
                # Search for similar documents
                similar_chunks = self.vector_store.search(
                    query_embedding=query_embedding,
                    limit=max_sources,
                    similarity_threshold=similarity_threshold
                )
                
                # Process retrieved chunks
                sources = []
                context_parts = []
                
                for chunk_id, similarity in similar_chunks:
                    chunk_data = self.vector_store.get_chunk_metadata(chunk_id)
                    if chunk_data:
                        sources.append({
                            "chunk_id": chunk_id,
                            "content": chunk_data.get('content', '')[:200] + "...",
                            "source_file": chunk_data.get('source_file', 'Unknown'),
                            "similarity_score": float(similarity)
                        })
                        
                        # Add full content to context
                        full_content = chunk_data.get('content', '')
                        if full_content:
                            context_parts.append(f"Source: {chunk_data.get('source_file', 'Unknown')}\n{full_content}")
                
                # Combine context, limiting total length
                context_text = "\n\n---\n\n".join(context_parts)
                if len(context_text) > self.config.max_context_length:
                    context_text = context_text[:self.config.max_context_length] + "...\n[Context truncated]"
                
                logger.info(f"Retrieved {len(sources)} relevant sources")
            
            # Step 2: Generate response with Ollama
            if use_context and context_text:
                # Create RAG prompt with context
                rag_prompt = self._create_rag_prompt(user_query, context_text, chat_history)
                response = self.ollama.generate(rag_prompt, self.config.rag_system_prompt)
            else:
                # Generate response without context
                messages = []
                if chat_history:
                    messages.extend(chat_history)
                messages.append({"role": "user", "content": user_query})
                response = self.ollama.chat(messages)
            
            response_time = (time.time() - start_time) * 1000
            
            result = RAGResult(
                response=response,
                sources=sources,
                context_used=context_text,
                response_time_ms=response_time,
                retrieval_count=len(sources)
            )
            
            logger.info(f"RAG query completed in {response_time:.2f}ms with {len(sources)} sources")
            return result
            
        except Exception as e:
            logger.error(f"RAG pipeline error: {str(e)}")
            response_time = (time.time() - start_time) * 1000
            
            return RAGResult(
                response="I apologize, but I encountered an error processing your request. Please try again.",
                sources=[],
                context_used="",
                response_time_ms=response_time,
                retrieval_count=0
            )
    
    def _create_rag_prompt(self, 
                          user_query: str, 
                          context: str, 
                          chat_history: Optional[List[Dict]] = None) -> str:
        """
        Create a RAG prompt with context and history
        
        Args:
            user_query: User's question
            context: Retrieved document context
            chat_history: Previous conversation
            
        Returns:
            Formatted prompt for the LLM
        """
        prompt_parts = []
        
        # Add chat history if available
        if chat_history:
            prompt_parts.append("Previous conversation:")
            for msg in chat_history[-3:]:  # Last 3 messages for context
                role = msg.get('role', '')
                content = msg.get('content', '')
                if role and content:
                    prompt_parts.append(f"{role.title()}: {content}")
            prompt_parts.append("")
        
        # Add document context
        prompt_parts.append("Based on the following context from the user's documents:")
        prompt_parts.append("---")
        prompt_parts.append(context)
        prompt_parts.append("---")
        prompt_parts.append("")
        
        # Add user question
        prompt_parts.append(f"Question: {user_query}")
        prompt_parts.append("")
        prompt_parts.append("Please provide a helpful and accurate answer based on the context above. If the context doesn't contain enough information to fully answer the question, please say so.")
        
        return "\n".join(prompt_parts)
    
    def simple_chat(self, 
                   user_message: str, 
                   chat_history: Optional[List[Dict]] = None) -> str:
        """
        Simple chat without document retrieval
        
        Args:
            user_message: User's message
            chat_history: Previous conversation
            
        Returns:
            AI response
        """
        try:
            messages = []
            
            # Add system prompt
            messages.append({
                "role": "system", 
                "content": "You are a helpful AI assistant. Be concise, helpful, and friendly."
            })
            
            # Add chat history
            if chat_history:
                messages.extend(chat_history[-5:])  # Last 5 messages
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            return self.ollama.chat(messages)
            
        except Exception as e:
            logger.error(f"Simple chat error: {str(e)}")
            return "I apologize, but I'm having trouble processing your message right now."
    
    def check_health(self) -> Dict[str, bool]:
        """Check health of all RAG components"""
        return {
            "ollama": self.ollama.is_healthy(),
            "vector_store": self.vector_store.get_chunk_count() >= 0,
            "embedder": self.embedder.get_embedding_dimension() > 0
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Get pipeline statistics"""
        return {
            "available_models": len(self.ollama.get_available_models()),
            "corpus_chunks": self.vector_store.get_chunk_count(),
            "corpus_files": len(self.vector_store.get_file_list()),
            "embedding_dimension": self.embedder.get_embedding_dimension()
        }
