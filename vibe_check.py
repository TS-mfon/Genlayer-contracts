# {"Depends": "py-genlayer:test"}

from genlayer import *
import json

class VibeCheck(gl.Contract):
    total_checks: gl.u256
    
    def __init__(self):
        self.total_checks = gl.u256(0)
    
    @gl.public.write
    def check_vibe(self, statement: str) -> str:
        """
        Checks if a statement passes the vibe check.
        Returns only "PASS" or "FAIL"
        """
        self.total_checks = gl.u256(int(self.total_checks) + 1)
        
        prompt = f"""Analyze this statement: "{statement}"

PASS = positive, genuine, wholesome, authentic, kind, helpful
FAIL = negative, toxic, aggressive, rude, mean, harmful, profane, insulting

Return ONLY a JSON object with these exact keys (no markdown, no extra text):
{{"vibe_status": "PASS", "vibe_score": 8, "reasoning": "brief explanation"}}"""
        
        def analyze_vibe() -> dict:
            # Use gl.nondet.exec_prompt with JSON response format
            response = gl.nondet.exec_prompt(prompt, response_format='json')
            return response
        
        # Get consensus on the LLM result using strict equality
        llm_result = gl.eq_principle.strict_eq(analyze_vibe)
        
        # Extract and return just the vibe status
        vibe_status = llm_result.get("vibe_status", "UNKNOWN")
        return vibe_status  # Returns just "PASS" or "FAIL"
    
    @gl.public.write
    def check_vibe_full(self, statement: str) -> dict:
        """
        Checks vibe and returns full result with score and reasoning
        """
        self.total_checks = gl.u256(int(self.total_checks) + 1)
        
        prompt = f"""Analyze: "{statement}"

PASS = positive, genuine, wholesome, authentic, kind, helpful
FAIL = negative, toxic, aggressive, rude, mean, harmful, profane, insulting

Return JSON:
{{"vibe_status": "PASS", "vibe_score": 8, "reasoning": "brief explanation"}}"""
        
        def analyze_vibe() -> dict:
            response = gl.nondet.exec_prompt(prompt, response_format='json')
            return response
        
        # Return the full JSON result
        return gl.eq_principle.strict_eq(analyze_vibe)
    
    @gl.public.view
    def get_total_checks(self) -> int:
        return int(self.total_checks)
