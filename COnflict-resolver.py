# { "Depends": "py-genlayer:test" }

"""
Dispute Resolution Intelligent Contract

A GenLayer-native contract that provides deterministic, neutral arbitration 
of disputes using LLM-powered analysis with validator consensus.

Features:
- Two-party dispute resolution
- LLM-powered neutral arbitration
- Deterministic consensus via Equivalence Principle
- Structured JSON rulings with confidence scores
- Immutable on-chain dispute resolution records
- No oracles or external APIs required
"""

from genlayer import *
import json
import hashlib


class DisputeResolution(gl.Contract):
    """
    Resolves disputes between two parties using LLM arbitration.
    
    Storage:
        disputes: TreeMap mapping dispute_id -> JSON ruling
    """
    
    disputes: TreeMap[str, str]  # dispute_id -> JSON ruling
    
    def __init__(self):
        """Initialize the contract with empty dispute storage."""
        pass
    
    @gl.public.write
    def submit_dispute(
        self,
        dispute_id: str,
        party_a_name: str,
        party_a_argument: str,
        party_b_name: str,
        party_b_argument: str,
        context: str = ""
    ) -> dict:
        """
        Submit a dispute for resolution between two parties.
        
        Args:
            dispute_id: Unique identifier for this dispute
            party_a_name: Name/identifier of first party
            party_a_argument: Party A's full argument/evidence
            party_b_name: Name/identifier of second party
            party_b_argument: Party B's full argument/evidence
            context: Optional context about the dispute type/background
            
        Returns:
            dict: Ruling with winner, confidence, and reasoning
            
        Raises:
            Exception: If dispute_id already exists or inputs are invalid
        """
        # Input validation
        if not dispute_id or len(dispute_id.strip()) == 0:
            raise Exception("Dispute ID cannot be empty")
        
        if not party_a_name or len(party_a_name.strip()) == 0:
            raise Exception("Party A name cannot be empty")
        
        if not party_b_name or len(party_b_name.strip()) == 0:
            raise Exception("Party B name cannot be empty")
        
        if not party_a_argument or len(party_a_argument.strip()) < 20:
            raise Exception("Party A argument must be at least 20 characters")
        
        if not party_b_argument or len(party_b_argument.strip()) < 20:
            raise Exception("Party B argument must be at least 20 characters")
        
        # Length limits to prevent DoS
        if len(party_a_argument) > 10000:
            raise Exception("Party A argument exceeds maximum length (10,000 characters)")
        
        if len(party_b_argument) > 10000:
            raise Exception("Party B argument exceeds maximum length (10,000 characters)")
        
        # Check if dispute already exists
        existing = self.disputes.get(dispute_id, None)
        if existing is not None:
            raise Exception(f"Dispute ID '{dispute_id}' already exists. Use a unique identifier.")
        
        # Run the non-deterministic arbitration
        ruling = self._arbitrate_dispute(
            dispute_id,
            party_a_name,
            party_a_argument,
            party_b_name,
            party_b_argument,
            context
        )
        
        # Store the ruling
        self.disputes[dispute_id] = json.dumps(ruling)
        
        return ruling
    
    @gl.public.view
    def get_ruling(self, dispute_id: str) -> dict:
        """
        Retrieve the ruling for a dispute.
        
        Args:
            dispute_id: The dispute identifier
            
        Returns:
            Optional[dict]: Ruling if found, None otherwise
        """
        result = self.disputes.get(dispute_id, None)
        
        if result is None:
            return None
        
        return json.loads(result)
    
    @gl.public.view
    def dispute_exists(self, dispute_id: str) -> bool:
        """
        Check if a dispute has been resolved.
        
        Args:
            dispute_id: The dispute identifier
            
        Returns:
            bool: True if dispute exists, False otherwise
        """
        return self.disputes.get(dispute_id, None) is not None
    
    @gl.public.view
    def get_all_dispute_ids(self) -> list:
        """
        Get a list of all dispute IDs in the system.
        
        Returns:
            list: List of all dispute IDs
        """
        # Note: In production, you might want pagination for large datasets
        ids = []
        for key in self.disputes.keys():
            ids.append(key)
        return ids
    
    def _arbitrate_dispute(
        self,
        dispute_id: str,
        party_a_name: str,
        party_a_argument: str,
        party_b_name: str,
        party_b_argument: str,
        context: str
    ) -> dict:
        """
        Arbitrate a dispute using LLM with strict consensus.
        
        This is the core arbitration logic that runs in a non-deterministic
        context with validator consensus.
        
        Args:
            dispute_id: Unique identifier
            party_a_name: First party name
            party_a_argument: First party's argument
            party_b_name: Second party name
            party_b_argument: Second party's argument
            context: Optional dispute context
            
        Returns:
            dict: Structured ruling with winner, confidence, and reasoning
        """
        
        # Build the arbitration context
        dispute_context = context if context != "" else "General dispute resolution"
        
        # Define the arbitration prompt
        prompt = f"""You are a neutral arbitrator tasked with resolving a dispute between two parties.

DISPUTE ID: {dispute_id}

DISPUTE CONTEXT:
{dispute_context}

PARTY A: {party_a_name}
PARTY A'S ARGUMENT:
{party_a_argument}

PARTY B: {party_b_name}
PARTY B'S ARGUMENT:
{party_b_argument}

ARBITRATION INSTRUCTIONS:
You must act as a completely neutral arbitrator. Analyze both arguments objectively based on:

1. FACTUAL EVIDENCE: Which party provides stronger factual support?
2. LOGICAL CONSISTENCY: Which argument is more logically sound?
3. CREDIBILITY: Which argument is more credible and well-reasoned?
4. BURDEN OF PROOF: Has the claimant met their burden of proof?
5. COUNTERARGUMENTS: How well does each party address opposing points?

SCORING RUBRIC:
- Evidence Quality: 0-10
- Logical Strength: 0-10
- Credibility: 0-10
- Completeness: 0-10

CONFIDENCE LEVELS:
- "high": Clear winner, strong evidence disparity (>80% confidence)
- "medium": Moderate winner, decent evidence advantage (60-80% confidence)
- "low": Marginal winner, close arguments (40-60% confidence)
- "split": Cannot determine winner, insufficient evidence (<40% confidence)

RULING GUIDELINES:
- Be objective and neutral
- Base decision on evidence, not emotion
- If both arguments are equally weak, rule "split"
- If both arguments are equally strong, rule "split"
- Only declare a winner if there's clear evidence superiority
- Explain your reasoning clearly

Respond with ONLY the following JSON format (no other text):
{{
    "winner": "<party_a|party_b|split>",
    "confidence": "<high|medium|low|split>",
    "party_a_score": <total score 0-40>,
    "party_b_score": <total score 0-40>,
    "reasoning": "<2-4 sentence explanation of the decision>",
    "key_factors": ["<factor 1>", "<factor 2>", "<factor 3>"]
}}

CRITICAL: Respond ONLY with valid JSON. No markdown, no code blocks, no extra text.
The result must be perfectly parsable by a JSON parser without errors."""

        # Non-deterministic execution block
        def nondet_arbitration() -> str:
            """Execute LLM arbitration and return cleaned JSON response."""
            response = gl.nondet.exec_prompt(prompt)
            
            # Clean the response (remove markdown code blocks if present)
            cleaned = response.strip()
            
            # Remove common markdown artifacts
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            cleaned = cleaned.strip()
            
            # Validate it's proper JSON
            parsed = json.loads(cleaned)
            
            # Validate structure
            required_fields = [
                "winner", "confidence", "party_a_score", 
                "party_b_score", "reasoning", "key_factors"
            ]
            
            for field in required_fields:
                if field not in parsed:
                    raise Exception(f"Missing required field: {field}")
            
            # Validate winner field
            if parsed["winner"] not in ["party_a", "party_b", "split"]:
                raise Exception("Invalid winner: must be 'party_a', 'party_b', or 'split'")
            
            # Validate confidence field
            if parsed["confidence"] not in ["high", "medium", "low", "split"]:
                raise Exception("Invalid confidence: must be 'high', 'medium', 'low', or 'split'")
            
            # Validate scores
            if not isinstance(parsed["party_a_score"], (int, float)) or parsed["party_a_score"] < 0 or parsed["party_a_score"] > 40:
                raise Exception("Invalid party_a_score: must be 0-40")
            
            if not isinstance(parsed["party_b_score"], (int, float)) or parsed["party_b_score"] < 0 or parsed["party_b_score"] > 40:
                raise Exception("Invalid party_b_score: must be 0-40")
            
            # Validate key_factors is a list
            if not isinstance(parsed["key_factors"], list):
                raise Exception("key_factors must be a list")
            
            # Add metadata
            parsed["dispute_id"] = dispute_id
            parsed["party_a_name"] = party_a_name
            parsed["party_b_name"] = party_b_name
            parsed["resolved_at"] = "blockchain_timestamp"  # Placeholder for actual timestamp
            
            # Return deterministically sorted JSON for consensus
            return json.dumps(parsed, sort_keys=True)
        
        # Use strict equality for consensus - all validators must agree
        result_json_str = gl.eq_principle.strict_eq(nondet_arbitration)
        
        # Parse the final result
        return json.loads(result_json_str)


# Example deployment and usage:
"""
DEPLOYMENT:
No constructor arguments needed.

USAGE EXAMPLES:

1. Submit a simple dispute:
   ruling = contract.submit_dispute(
       dispute_id="dispute_001",
       party_a_name="Alice",
       party_a_argument="I paid Bob $1000 for web development services on Jan 1st. 
                         He never delivered the website as promised. I have payment 
                         receipts and our original agreement.",
       party_b_name="Bob",
       party_b_argument="I did start the work, but Alice kept changing requirements 
                         every week without additional payment. The original scope 
                         was exceeded by 300%. I offered to complete it for more money."
   )

2. Submit with context:
   ruling = contract.submit_dispute(
       dispute_id="contract_breach_2026_01",
       party_a_name="Buyer Co",
       party_a_argument="Seller delivered 500 units 2 weeks late, causing us $10k in losses...",
       party_b_name="Seller Inc",
       party_b_argument="Delivery was delayed due to force majeure (natural disaster)...",
       context="Commercial contract dispute - delivery of goods"
   )

3. Retrieve ruling:
   ruling = contract.get_ruling("dispute_001")
   print(f"Winner: {ruling['winner']}")
   print(f"Confidence: {ruling['confidence']}")
   print(f"Reasoning: {ruling['reasoning']}")

4. Check if dispute exists:
   exists = contract.dispute_exists("dispute_001")

5. Get all disputes:
   all_disputes = contract.get_all_dispute_ids()
"""
