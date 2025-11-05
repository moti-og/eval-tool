"""
Integration helper for OpenGov application

Use this to capture LLM responses from your OpenGov app and queue them for review.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class OpenGovReviewCapture:
    """
    Capture LLM responses from OpenGov application for human review
    
    Usage in your OpenGov application:
    
        from opengov_integration import capture_for_review
        
        # After getting LLM response:
        response = llm.generate(prompt, context)
        
        # Capture for review:
        capture_for_review(
            prompt=prompt,
            context=context,
            response=response,
            feature="budget_analysis",
            model="gpt-4",
            user_id=user.id
        )
    """
    
    def __init__(self, pending_file: str = "review_data/pending_reviews.json"):
        self.pending_file = Path(pending_file)
        self.pending_file.parent.mkdir(exist_ok=True)
        
        if not self.pending_file.exists():
            self.pending_file.write_text("[]")
    
    def capture(
        self,
        prompt: str,
        response: str,
        context: Optional[str] = None,
        expected_output: Optional[str] = None,
        feature: Optional[str] = None,
        model: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Capture an LLM response for human review
        
        Args:
            prompt: The prompt sent to the LLM
            response: The LLM's response
            context: Additional context provided to the LLM
            expected_output: Expected/ideal output (if known)
            feature: What feature this is for (e.g., "budget_analysis", "report_generation")
            model: Model used (e.g., "gpt-4", "claude-3")
            user_id: User who triggered this (for tracking)
            metadata: Any additional metadata
            
        Returns:
            review_id: Unique ID for this review
        """
        
        # Generate unique ID
        review_id = str(uuid.uuid4())
        
        # Create review record
        review_record = {
            "id": review_id,
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "context": context,
            "expected_output": expected_output,
            "feature": feature,
            "model": model,
            "user_id": user_id,
            "metadata": metadata or {}
        }
        
        # Load existing pending reviews
        with open(self.pending_file) as f:
            pending = json.load(f)
        
        # Add new review
        pending.append(review_record)
        
        # Save back
        with open(self.pending_file, 'w') as f:
            json.dump(pending, f, indent=2)
        
        return review_id
    
    def capture_with_sampling(
        self,
        prompt: str,
        response: str,
        sample_rate: float = 0.1,
        **kwargs
    ) -> Optional[str]:
        """
        Capture with sampling (only capture X% of responses)
        
        Args:
            prompt: The prompt
            response: The response
            sample_rate: Percentage to capture (0.0 to 1.0)
            **kwargs: Other arguments passed to capture()
            
        Returns:
            review_id if captured, None if skipped
        """
        import random
        
        if random.random() < sample_rate:
            return self.capture(prompt, response, **kwargs)
        
        return None
    
    def capture_on_error(
        self,
        prompt: str,
        response: str,
        error_indicator: str,
        **kwargs
    ) -> Optional[str]:
        """
        Only capture responses that might have errors
        
        Args:
            prompt: The prompt
            response: The response
            error_indicator: Text that indicates potential error
            **kwargs: Other arguments
            
        Returns:
            review_id if captured, None if no error detected
        """
        if error_indicator.lower() in response.lower():
            kwargs['metadata'] = kwargs.get('metadata', {})
            kwargs['metadata']['flagged_reason'] = 'error_indicator'
            return self.capture(prompt, response, **kwargs)
        
        return None
    
    def get_pending_count(self) -> int:
        """Get count of pending reviews"""
        with open(self.pending_file) as f:
            return len(json.load(f))


# Convenience function for easy import
_capturer = OpenGovReviewCapture()


def capture_for_review(
    prompt: str,
    response: str,
    **kwargs
) -> str:
    """
    Simple function to capture a response for review
    
    Example:
        from opengov_integration import capture_for_review
        
        response = llm.generate("What is the budget?")
        capture_for_review(
            prompt="What is the budget?",
            response=response,
            feature="budget_query"
        )
    """
    return _capturer.capture(prompt, response, **kwargs)


def capture_sample(
    prompt: str,
    response: str,
    sample_rate: float = 0.1,
    **kwargs
) -> Optional[str]:
    """
    Capture only X% of responses (for high-volume features)
    
    Example:
        # Only capture 10% of responses for review
        capture_sample(
            prompt=prompt,
            response=response,
            sample_rate=0.1,
            feature="frequent_query"
        )
    """
    return _capturer.capture_with_sampling(prompt, response, sample_rate, **kwargs)


# Decorator for easy integration
def review_llm_response(feature: str, sample_rate: float = 1.0):
    """
    Decorator to automatically capture LLM responses for review
    
    Example:
        @review_llm_response(feature="budget_analysis", sample_rate=0.2)
        def generate_budget_analysis(prompt: str, context: str) -> str:
            response = llm.generate(prompt, context)
            return response
        
        # Usage:
        result = generate_budget_analysis("Analyze Q1", context_data)
        # Automatically captured for review (20% of the time)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Call original function
            result = func(*args, **kwargs)
            
            # Try to extract prompt from args/kwargs
            prompt = kwargs.get('prompt') or (args[0] if args else "")
            context = kwargs.get('context', None)
            
            # Capture for review
            if sample_rate >= 1.0 or _capturer.capture_with_sampling(
                prompt=str(prompt),
                response=str(result),
                context=str(context) if context else None,
                feature=feature,
                sample_rate=sample_rate
            ):
                pass  # Captured
            
            return result
        
        return wrapper
    return decorator

