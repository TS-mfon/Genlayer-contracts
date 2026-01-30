# {"Depends": "py-genlayer:test"}

from genlayer import *
import json

class VibeCheck(gl.Contract):
    total_checks: gl.u256
    
    def __init__(self):
        self.total_checks = gl.u256(0)
    
    @gl.public.write
    def check_vibe(self, statement: str) -> str:
        """Checks if a statement passes the vibe check"""
        self.total_checks = gl.u256(int(self.total_checks) + 1)
        
        prompt = f"""Analyze this statement: "{statement}"

PASS = positive, genuine, wholesome, authentic
FAIL = negative, toxic, forced, fake

Respond using ONLY this format (no markdown):
{{"vibe_status": "PASS", "vibe_score": 8, "reasoning": "explanation"}}

It is mandatory that you respond only using the JSON format above, nothing else."""
        
        def analyze_vibe() -> str:
            return prompt
        
        vibe_result = gl.eq_principle.prompt_comparative(
            analyze_vibe,
            principle="Both results should have the same vibe_status (PASS or FAIL)"
        )
        return vibe_result
    
    @gl.public.view
    def get_total_checks(self) -> int:
        return int(self.total_checks)
