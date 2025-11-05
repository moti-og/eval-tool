"""
LLM Evaluation Framework
"""

from .connectors import BaseConnector, OpenAIConnector, AnthropicConnector, CustomAppConnector
from .evaluators import evaluate_result, EVALUATOR_REGISTRY
from .runners import TestRunner
from .results import ResultsManager

__all__ = [
    'BaseConnector',
    'OpenAIConnector', 
    'AnthropicConnector',
    'CustomAppConnector',
    'evaluate_result',
    'EVALUATOR_REGISTRY',
    'TestRunner',
    'ResultsManager',
]

