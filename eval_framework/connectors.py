"""
Connectors for different systems (LLMs, APIs, custom applications)
"""

import os
import requests
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod


class BaseConnector(ABC):
    """Base class for all connectors"""
    
    @abstractmethod
    def call(self, input_data: Any, **kwargs) -> str:
        """
        Call the system and return the output
        
        Args:
            input_data: Input to send to the system
            **kwargs: Additional parameters
            
        Returns:
            String output from the system
        """
        pass


class OpenAIConnector(BaseConnector):
    """Connector for OpenAI API"""
    
    def __init__(self, model: str = "gpt-4", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def call(self, input_data: Any, system_prompt: Optional[str] = None, **kwargs) -> str:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": str(input_data)})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        
        return response.choices[0].message.content


class AnthropicConnector(BaseConnector):
    """Connector for Anthropic API"""
    
    def __init__(self, model: str = "claude-3-5-sonnet-20241022", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def call(self, input_data: Any, system_prompt: Optional[str] = None, **kwargs) -> str:
        params = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "messages": [{"role": "user", "content": str(input_data)}]
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        response = self.client.messages.create(**params)
        
        return response.content[0].text


class CustomAppConnector(BaseConnector):
    """
    Connector for your custom application
    
    Modify this to integrate with your actual application!
    """
    
    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or os.getenv("APP_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.getenv("APP_API_KEY")
    
    def call(self, input_data: Any, endpoint: str = "/api/process", **kwargs) -> str:
        """
        Call your custom application
        
        CUSTOMIZE THIS METHOD to match your application's API!
        
        Examples:
        - REST API call
        - gRPC call
        - CLI command execution
        - Direct function call
        """
        
        # Example: REST API call
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = requests.post(
                url,
                json={"input": input_data, **kwargs},
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get("output", response.text)
        except requests.exceptions.RequestException as e:
            return f"Error calling application: {str(e)}"


class MockConnector(BaseConnector):
    """Mock connector for testing the eval framework itself"""
    
    def __init__(self, response: str = "Mock response"):
        self.response = response
    
    def call(self, input_data: Any, **kwargs) -> str:
        return f"{self.response}: {input_data}"


# Registry of available connectors
CONNECTOR_REGISTRY = {
    "openai": OpenAIConnector,
    "anthropic": AnthropicConnector,
    "custom_app": CustomAppConnector,
    "mock": MockConnector,
}


def get_connector(connector_type: str, **kwargs) -> BaseConnector:
    """
    Factory function to get a connector instance
    
    Args:
        connector_type: Type of connector ("openai", "anthropic", "custom_app", etc.)
        **kwargs: Arguments to pass to the connector constructor
        
    Returns:
        Connector instance
    """
    if connector_type not in CONNECTOR_REGISTRY:
        raise ValueError(
            f"Unknown connector type: {connector_type}. "
            f"Available: {list(CONNECTOR_REGISTRY.keys())}"
        )
    
    return CONNECTOR_REGISTRY[connector_type](**kwargs)

