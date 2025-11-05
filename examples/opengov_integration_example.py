"""
Example: Integrating human review into OpenGov application

This shows how to capture LLM responses from your OpenGov app for human review.
"""

from opengov_integration import capture_for_review, capture_sample, review_llm_response
from typing import Dict


# Example 1: Basic capture after LLM call
def budget_analysis_basic(user_query: str, budget_data: Dict) -> str:
    """
    Example OpenGov feature: Budget Analysis
    """
    # Prepare prompt and context
    prompt = f"Analyze this budget request: {user_query}"
    context = f"Budget data: {budget_data}"
    
    # Call your LLM (replace with actual OpenGov LLM call)
    response = call_openai_gpt4(prompt, context)
    
    # Capture for human review
    capture_for_review(
        prompt=prompt,
        context=context,
        response=response,
        feature="budget_analysis",
        model="gpt-4",
        user_id="user_123"
    )
    
    return response


# Example 2: Sampling (for high-volume features)
def frequent_query_handler(query: str) -> str:
    """
    For features that get called frequently, only capture 10% for review
    """
    prompt = query
    response = call_your_llm(prompt)
    
    # Only capture 10% of responses
    capture_sample(
        prompt=prompt,
        response=response,
        sample_rate=0.1,  # 10%
        feature="frequent_queries"
    )
    
    return response


# Example 3: Using decorator for automatic capture
@review_llm_response(feature="report_generation", sample_rate=0.2)
def generate_financial_report(report_type: str, context: str) -> str:
    """
    Automatically captures 20% of responses for review
    """
    prompt = f"Generate {report_type} report"
    response = call_your_llm(prompt, context)
    return response


# Example 4: Conditional capture (only on errors or edge cases)
def smart_capture(user_input: str) -> str:
    """
    Only capture responses that might need review
    """
    from opengov_integration import OpenGovReviewCapture
    
    capturer = OpenGovReviewCapture()
    
    response = call_your_llm(user_input)
    
    # Capture if response seems problematic
    if any(indicator in response.lower() for indicator in ['error', 'unknown', 'cannot', 'unclear']):
        capturer.capture(
            prompt=user_input,
            response=response,
            feature="smart_query",
            metadata={"flagged": True, "reason": "potential_issue"}
        )
    
    # Or capture if input is complex
    elif len(user_input) > 500:
        capturer.capture_with_sampling(
            prompt=user_input,
            response=response,
            sample_rate=0.5,  # 50% for complex queries
            feature="complex_query"
        )
    
    return response


# Example 5: Full OpenGov workflow integration
class OpenGovBudgetAssistant:
    """
    Example integration into OpenGov's budget assistant feature
    """
    
    def __init__(self):
        from opengov_integration import OpenGovReviewCapture
        self.review_capturer = OpenGovReviewCapture()
    
    def analyze_budget_variance(self, department: str, quarter: str) -> Dict:
        """
        Analyze budget variance for a department
        """
        # Build prompt
        prompt = f"Analyze budget variance for {department} in {quarter}"
        
        # Get context from OpenGov database
        context = self.get_budget_context(department, quarter)
        
        # Call LLM
        response = self.call_llm(prompt, context)
        
        # Parse response
        analysis = self.parse_response(response)
        
        # Capture for review if variance is significant
        if analysis.get('variance_percent', 0) > 10:
            self.review_capturer.capture(
                prompt=prompt,
                context=str(context),
                response=response,
                feature="budget_variance_analysis",
                model="gpt-4",
                metadata={
                    "department": department,
                    "quarter": quarter,
                    "variance_percent": analysis['variance_percent'],
                    "flagged": True
                }
            )
        
        return analysis
    
    def get_budget_context(self, department: str, quarter: str) -> Dict:
        """Mock: Get budget data from OpenGov database"""
        return {
            "department": department,
            "quarter": quarter,
            "budget": 1000000,
            "actual": 1150000
        }
    
    def call_llm(self, prompt: str, context: Dict) -> str:
        """Mock: Call your LLM"""
        return f"Budget variance analysis: {context['department']} is 15% over budget"
    
    def parse_response(self, response: str) -> Dict:
        """Mock: Parse LLM response"""
        return {
            "variance_percent": 15,
            "analysis": response
        }


# Mock LLM functions (replace with your actual implementations)
def call_openai_gpt4(prompt: str, context: str) -> str:
    """Replace with your actual OpenAI call"""
    return f"Analysis based on: {prompt[:50]}..."


def call_your_llm(prompt: str, context: str = None) -> str:
    """Replace with your actual LLM call"""
    return f"Response to: {prompt[:50]}..."


# Example usage
if __name__ == '__main__':
    # Example 1: Basic usage
    result = budget_analysis_basic(
        "What's our Q1 spending?",
        {"q1_budget": 1000000, "q1_actual": 950000}
    )
    print(f"Result 1: {result}")
    
    # Example 2: High-volume with sampling
    result = frequent_query_handler("What is the budget for IT?")
    print(f"Result 2: {result}")
    
    # Example 3: Using decorator
    result = generate_financial_report("quarterly", "Q1 2024")
    print(f"Result 3: {result}")
    
    # Example 4: Smart conditional capture
    result = smart_capture("This is a complex query about budget forecasting...")
    print(f"Result 4: {result}")
    
    # Example 5: Full workflow
    assistant = OpenGovBudgetAssistant()
    result = assistant.analyze_budget_variance("Engineering", "Q1")
    print(f"Result 5: {result}")
    
    # Check how many reviews are pending
    from opengov_integration import _capturer
    print(f"\nPending reviews: {_capturer.get_pending_count()}")
    print("\nRun 'streamlit run human_review_app.py' to review these responses!")

