"""
Evaluation logic for scoring and validating outputs
"""

import re
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class EvalResult:
    """Result of a single evaluation"""
    passed: bool
    score: float  # 0.0 to 1.0
    evaluator_type: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseEvaluator:
    """Base class for evaluators"""
    
    def evaluate(self, output: str, expected: Optional[str] = None, **kwargs) -> EvalResult:
        """
        Evaluate the output
        
        Args:
            output: The actual output from the system
            expected: Expected output (if applicable)
            **kwargs: Additional parameters for the evaluator
            
        Returns:
            EvalResult with pass/fail, score, and details
        """
        raise NotImplementedError


class ExactMatchEvaluator(BaseEvaluator):
    """Exact string match"""
    
    def evaluate(self, output: str, expected: Optional[str] = None, **kwargs) -> EvalResult:
        if expected is None:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="exact_match",
                error="No expected output provided"
            )
        
        passed = output.strip() == expected.strip()
        return EvalResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            evaluator_type="exact_match"
        )


class ContainsEvaluator(BaseEvaluator):
    """Check if output contains specific text"""
    
    def evaluate(self, output: str, expected: Optional[str] = None, value: Optional[str] = None, **kwargs) -> EvalResult:
        search_text = value or expected
        
        if search_text is None:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="contains",
                error="No search text provided"
            )
        
        passed = search_text.lower() in output.lower()
        return EvalResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            evaluator_type="contains",
            details={"searched_for": search_text}
        )


class RegexEvaluator(BaseEvaluator):
    """Regular expression matching"""
    
    def evaluate(self, output: str, pattern: Optional[str] = None, **kwargs) -> EvalResult:
        if pattern is None:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="regex",
                error="No pattern provided"
            )
        
        try:
            match = re.search(pattern, output, re.IGNORECASE)
            passed = match is not None
            return EvalResult(
                passed=passed,
                score=1.0 if passed else 0.0,
                evaluator_type="regex",
                details={"pattern": pattern, "match": match.group(0) if match else None}
            )
        except re.error as e:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="regex",
                error=f"Invalid regex pattern: {str(e)}"
            )


class SemanticSimilarityEvaluator(BaseEvaluator):
    """Semantic similarity using embeddings"""
    
    def __init__(self):
        self._model = None
    
    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer('all-MiniLM-L6-v2')
            except ImportError:
                raise ImportError(
                    "sentence-transformers not installed. "
                    "Run: pip install sentence-transformers"
                )
        return self._model
    
    def evaluate(self, output: str, expected: Optional[str] = None, threshold: float = 0.8, **kwargs) -> EvalResult:
        if expected is None:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="semantic_similarity",
                error="No expected output provided"
            )
        
        try:
            model = self._get_model()
            from sklearn.metrics.pairwise import cosine_similarity
            
            embeddings = model.encode([output, expected])
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            passed = similarity >= threshold
            return EvalResult(
                passed=passed,
                score=float(similarity),
                evaluator_type="semantic_similarity",
                details={
                    "similarity": float(similarity),
                    "threshold": threshold
                }
            )
        except Exception as e:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="semantic_similarity",
                error=f"Error computing similarity: {str(e)}"
            )


class JSONSchemaEvaluator(BaseEvaluator):
    """Validate JSON structure"""
    
    def evaluate(self, output: str, schema: Optional[Dict] = None, **kwargs) -> EvalResult:
        try:
            parsed = json.loads(output)
            
            if schema:
                # Simple schema validation - check if required keys exist
                required_keys = schema.get("required", [])
                missing_keys = [key for key in required_keys if key not in parsed]
                
                if missing_keys:
                    return EvalResult(
                        passed=False,
                        score=0.5,
                        evaluator_type="json_schema",
                        details={"missing_keys": missing_keys}
                    )
            
            return EvalResult(
                passed=True,
                score=1.0,
                evaluator_type="json_schema",
                details={"parsed": parsed}
            )
        except json.JSONDecodeError as e:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="json_schema",
                error=f"Invalid JSON: {str(e)}"
            )


class LengthEvaluator(BaseEvaluator):
    """Check output length constraints"""
    
    def evaluate(self, output: str, min_length: Optional[int] = None, max_length: Optional[int] = None, **kwargs) -> EvalResult:
        length = len(output)
        passed = True
        details = {"length": length}
        
        if min_length is not None:
            passed = passed and length >= min_length
            details["min_length"] = min_length
        
        if max_length is not None:
            passed = passed and length <= max_length
            details["max_length"] = max_length
        
        return EvalResult(
            passed=passed,
            score=1.0 if passed else 0.0,
            evaluator_type="length",
            details=details
        )


class CustomEvaluator(BaseEvaluator):
    """Custom evaluation function"""
    
    def __init__(self, func: Callable):
        self.func = func
    
    def evaluate(self, output: str, expected: Optional[str] = None, **kwargs) -> EvalResult:
        try:
            result = self.func(output, expected, **kwargs)
            
            # If function returns a boolean, convert to EvalResult
            if isinstance(result, bool):
                return EvalResult(
                    passed=result,
                    score=1.0 if result else 0.0,
                    evaluator_type="custom"
                )
            
            # If function returns a dict, convert to EvalResult
            if isinstance(result, dict):
                return EvalResult(
                    passed=result.get("passed", False),
                    score=result.get("score", 0.0),
                    evaluator_type="custom",
                    details=result.get("details")
                )
            
            # If function returns EvalResult directly, use it
            if isinstance(result, EvalResult):
                return result
            
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="custom",
                error="Custom function returned invalid type"
            )
        except Exception as e:
            return EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="custom",
                error=f"Custom evaluator error: {str(e)}"
            )


# Registry of evaluators
EVALUATOR_REGISTRY = {
    "exact_match": ExactMatchEvaluator,
    "contains": ContainsEvaluator,
    "regex": RegexEvaluator,
    "semantic_similarity": SemanticSimilarityEvaluator,
    "json_schema": JSONSchemaEvaluator,
    "length": LengthEvaluator,
}


def evaluate_result(
    output: str,
    evaluators: List[Dict[str, Any]],
    expected: Optional[str] = None,
    custom_evaluators: Optional[Dict[str, Callable]] = None
) -> List[EvalResult]:
    """
    Evaluate output against multiple evaluators
    
    Args:
        output: The actual output from the system
        evaluators: List of evaluator configs (e.g., [{"type": "exact_match"}, {"type": "contains", "value": "test"}])
        expected: Expected output (if applicable)
        custom_evaluators: Dict of custom evaluator functions
        
    Returns:
        List of EvalResult objects
    """
    results = []
    custom_evaluators = custom_evaluators or {}
    
    for eval_config in evaluators:
        eval_type = eval_config.get("type")
        
        if not eval_type:
            results.append(EvalResult(
                passed=False,
                score=0.0,
                evaluator_type="unknown",
                error="No evaluator type specified"
            ))
            continue
        
        # Check if it's a custom evaluator
        if eval_type == "custom":
            func_name = eval_config.get("function")
            if func_name and func_name in custom_evaluators:
                evaluator = CustomEvaluator(custom_evaluators[func_name])
            else:
                results.append(EvalResult(
                    passed=False,
                    score=0.0,
                    evaluator_type="custom",
                    error=f"Custom function '{func_name}' not found"
                ))
                continue
        elif eval_type in EVALUATOR_REGISTRY:
            evaluator = EVALUATOR_REGISTRY[eval_type]()
        else:
            results.append(EvalResult(
                passed=False,
                score=0.0,
                evaluator_type=eval_type,
                error=f"Unknown evaluator type: {eval_type}"
            ))
            continue
        
        # Run the evaluation
        eval_kwargs = {k: v for k, v in eval_config.items() if k != "type"}
        result = evaluator.evaluate(output, expected, **eval_kwargs)
        results.append(result)
    
    return results

