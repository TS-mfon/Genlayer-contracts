# {"Depends": "py-genlayer:test"}

from genlayer import *
import json

class CodeReviewJudge(gl.Contract):
    """
    AI Code Review Judge - Analyzes code quality and provides scores
    Evaluates readability, security, efficiency, and best practices
    """
    
    total_reviews: gl.u256
    
    def __init__(self):
        self.total_reviews = gl.u256(0)
    
    @gl.public.write
    def review_code(self, code: str, language: str) -> str:
        """
        Review code and return quality score
        
        Args:
            code: The code snippet to review
            language: Programming language (python, javascript, solidity, etc.)
            
        Returns:
            Score from 1-10
        """
        self.total_reviews = gl.u256(int(self.total_reviews) + 1)
        
        prompt = f"""You are an expert code reviewer analyzing {language} code.

CODE TO REVIEW:
```{language}
{code}
```

Analyze this code for:
1. Readability (clear variable names, comments, structure)
2. Security (vulnerabilities, safe practices)
3. Efficiency (performance, algorithms)
4. Best Practices (follows conventions, maintainability)

Return ONLY JSON (no markdown):
{{
    "score": 7,
    "readability": 8,
    "security": 7,
    "efficiency": 6,
    "best_practices": 8,
    "summary": "brief 1-2 sentence summary",
    "top_issues": ["issue 1", "issue 2", "issue 3"],
    "strengths": ["strength 1", "strength 2"]
}}

Score range: 1 (very poor) to 10 (excellent)"""
        
        def analyze_code() -> dict:
            response = gl.nondet.exec_prompt(prompt, response_format='json')
            return response
        
        result = gl.eq_principle.strict_eq(analyze_code)
        return str(result.get("score", 5))
    
    @gl.public.write
    def review_code_full(self, code: str, language: str) -> dict:
        """Returns full review with detailed feedback"""
        self.total_reviews = gl.u256(int(self.total_reviews) + 1)
        
        prompt = f"""Review this {language} code comprehensively.

CODE:
```{language}
{code}
```

Provide detailed analysis.

Return JSON:
{{
    "score": 7,
    "readability": 8,
    "security": 7,
    "efficiency": 6,
    "best_practices": 8,
    "summary": "overall assessment",
    "top_issues": ["critical issues to fix"],
    "strengths": ["what's done well"],
    "improvements": ["specific suggestions"]
}}"""
        
        def analyze_code() -> dict:
            response = gl.nondet.exec_prompt(prompt, response_format='json')
            return response
        
        return gl.eq_principle.strict_eq(analyze_code)
    
    @gl.public.view
    def get_total_reviews(self) -> int:
        return int(self.total_reviews)
