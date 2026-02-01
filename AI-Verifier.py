# {"Depends": "py-genlayer:test"}

from genlayer import *
import json

class AINotary(gl.Contract):
    """
    AI Notary - Verifies and records online events
    Based on GenLayer v0.1.3+ API
    
     WORKS WITH:
    - News sites, GitHub, company websites
    - CoinGecko, CoinMarketCap, documentation
    
     BLOCKED:
    - X/Twitter, Facebook, Instagram (use notarize_without_url)
    """
    
    total_notarizations: gl.u256
    
    def __init__(self):
        self.total_notarizations = gl.u256(0)
    
    @gl.public.write
    def notarize_event(self, claim: str, source_url: str) -> str:
        """
        Verifies if claim is supported by web content
        
        Returns: "VERIFIED" or "UNVERIFIED"
        """
        self.total_notarizations = gl.u256(int(self.total_notarizations) + 1)
        
        # Block social media
        blocked = ['x.com', 'twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com']
        if any(domain in source_url.lower() for domain in blocked):
            return "ERROR: Social media blocked - use notarize_without_url() instead"
        
        def fetch_and_verify() -> str:
            # CORRECT API: gl.nondet.web.render() from v0.1.3+
            web_content = gl.nondet.web.render(source_url, mode='text')
            
            # Verify with LLM
            prompt = f"""You are a notary verifying claims.

CLAIM TO VERIFY: "{claim}"

WEB CONTENT FROM {source_url}:
{web_content[:3000]}

Does the web content support this claim?

Return ONLY JSON (no markdown):
{{"status": "VERIFIED", "confidence": 90, "reasoning": "brief explanation"}}

Status must be "VERIFIED" or "UNVERIFIED"."""
            
            result = gl.nondet.exec_prompt(prompt, response_format='json')
            return result.get("status", "UNKNOWN")
        
        return gl.eq_principle.strict_eq(fetch_and_verify)
    
    @gl.public.write
    def notarize_event_full(self, claim: str, source_url: str) -> dict:
        """
        Full verification with confidence score and reasoning
        """
        self.total_notarizations = gl.u256(int(self.total_notarizations) + 1)
        
        # Block social media
        blocked = ['x.com', 'twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com']
        if any(domain in source_url.lower() for domain in blocked):
            return {
                "status": "ERROR",
                "reasoning": "Social media blocked. Use: CoinGecko, news sites, GitHub, or notarize_without_url()"
            }
        
        def fetch_and_verify() -> dict:
            # CORRECT API: gl.nondet.web.render()
            web_content = gl.nondet.web.render(source_url, mode='text')
            
            # Verify with LLM
            prompt = f"""Verify this claim against web content.

CLAIM: "{claim}"
SOURCE: {source_url}

WEB CONTENT:
{web_content[:3000]}

Analyze if the claim is accurate.

Return JSON:
{{"status": "VERIFIED", "confidence": 90, "reasoning": "detailed explanation", "key_evidence": "relevant quote from content"}}

Status: VERIFIED or UNVERIFIED
Confidence: 0-100"""
            
            result = gl.nondet.exec_prompt(prompt, response_format='json')
            return result
        
        return gl.eq_principle.strict_eq(fetch_and_verify)
    
    @gl.public.write
    def notarize_without_url(self, claim: str, evidence_text: str) -> dict:
        """
        Notarize by providing evidence directly (perfect for X/Twitter!)
        
        Args:
            claim: Your claim
            evidence_text: Paste the tweet/post text here
        """
        self.total_notarizations = gl.u256(int(self.total_notarizations) + 1)
        
        prompt = f"""Verify claim against provided evidence.

CLAIM: "{claim}"

EVIDENCE PROVIDED BY USER:
{evidence_text}

Does this evidence support the claim?

Return JSON:
{{"status": "VERIFIED", "confidence": 85, "reasoning": "explanation"}}"""
        
        def verify() -> dict:
            result = gl.nondet.exec_prompt(prompt, response_format='json')
            return result
        
        return gl.eq_principle.strict_eq(verify)
    
    @gl.public.view
    def get_total_notarizations(self) -> int:
        return int(self.total_notarizations)
