"""
Ollama integration for local LLM inference
"""
import logging
import requests
import json
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Chat message structure for Ollama"""
    role: str  # "user", "assistant", "system"
    content: str

class OllamaClient:
    """
    Client for interacting with Ollama API
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2"):
        """
        Initialize Ollama client
          Args:
            base_url: Ollama API base URL
            model: Model name to use for inference
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.session = requests.Session()
        # Configure default timeout for requests
        self.timeout = 60  # 60 second timeout
        
        # Test connection on initialization
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test if Ollama is running and accessible"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                logger.info(f"Connected to Ollama. Available models: {model_names}")
                
                if self.model not in model_names:
                    logger.warning(f"Model '{self.model}' not found. Available: {model_names}")
                    if model_names:
                        self.model = model_names[0]
                        logger.info(f"Using model: {self.model}")
                    else:
                        logger.error("No models available in Ollama")
                        return False
                
                return True
            else:
                logger.error(f"Ollama API returned status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Ollama: {str(e)}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate a response from Ollama
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Returns:
            Generated response text
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return "Sorry, I encountered an error generating a response."
                
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Sorry, I'm having trouble connecting to the AI model."
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """
        Chat with conversation history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Randomness in response (0.0 - 1.0)
            
        Returns:
            Assistant response
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', '')
            else:
                logger.error(f"Chat API error: {response.status_code} - {response.text}")
                return "Sorry, I encountered an error during our conversation."
                
        except Exception as e:
            logger.error(f"Error in chat: {str(e)}")
            return "Sorry, I'm having trouble processing your message."
    
    def stream_generate(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        """
        Generate streaming response from Ollama
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            
        Yields:
            Response chunks as they're generated
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 2048
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            if 'message' in chunk and 'content' in chunk['message']:
                                content = chunk['message']['content']
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
            else:
                logger.error(f"Stream API error: {response.status_code}")
                yield "Sorry, I encountered an error generating a response."
                
        except Exception as e:
            logger.error(f"Error in stream generation: {str(e)}")
            yield "Sorry, I'm having trouble connecting to the AI model."
    
    def get_available_models(self) -> List[str]:
        """Get list of available models in Ollama"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [m['name'] for m in models]
            else:
                logger.error(f"Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a model if it's not available
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            True if successful
        """
        try:
            payload = {"name": model_name}
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully pulled model: {model_name}")
                return True
            else:
                logger.error(f"Failed to pull model: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error pulling model: {str(e)}")
            return False
    
    def is_healthy(self) -> bool:
        """Check if Ollama service is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class OllamaConfig:
    """Configuration for Ollama integration"""
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.default_model = "llama3.2"
        self.chat_model = "llama3.2" 
        self.temperature = 0.7
        self.max_tokens = 2048
        self.timeout = 60
        
        # RAG-specific settings
        self.rag_system_prompt = """You are a helpful research assistant. You have access to a user's document corpus and can answer questions based on the provided context. 

When answering:
1. Use the provided context to answer questions accurately
2. If the context doesn't contain relevant information, say so clearly
3. Cite sources when possible
4. Be concise but thorough
5. If asked about something not in the context, acknowledge the limitation

Always be helpful, honest, and precise in your responses."""
        
        self.max_context_length = 4000  # Max chars for context injection
