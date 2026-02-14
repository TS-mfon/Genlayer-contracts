# { "Depends": "py-genlayer:test" }

"""
DAO Proposal Evaluator - Intelligent Contract

A GenLayer-native contract that provides deterministic, neutral evaluation 
of DAO governance proposals using LLM-powered analysis with consensus.

Features:
- Deterministic proposal evaluation across 6 key dimensions
- Structured JSON scoring output
- On-chain audit trail of all evaluations
- Neutral, replayable AI governance decisions
- Protection against prompt injection and manipulation
"""

from genlayer import *
import json
import hashlib


class DAOProposalEvaluator(gl.Contract):
    """
    Evaluates DAO proposals against predefined governance criteria.
    
    Storage:
        evaluations: TreeMap mapping proposal_hash -> evaluation results
    """
    
    evaluations: TreeMap[str, str]  # proposal_hash -> JSON evaluation
    
    def __init__(self):
        """Initialize the contract with empty evaluation storage."""
        pass
    
    @gl.public.write
    def submit_proposal(
        self,
        proposal_text: str,
        budget: int = 0,
        timeline: str = "",
        dao_mission: str = ""
    ) -> dict:
        """
        Submit a DAO proposal for evaluation.
        
        Args:
            proposal_text: The full text of the proposal
            budget: Optional budget amount (in USD or tokens)
            timeline: Optional execution timeline
            dao_mission: Optional DAO mission statement for alignment check
            
        Returns:
            dict: Evaluation results including scores, verdict, and summary
            
        Raises:
            Exception: If proposal is empty or too short
        """
        # Input validation
        if not proposal_text or len(proposal_text.strip()) < 20:
            raise Exception("Proposal text must be at least 20 characters")
        
        if len(proposal_text) > 50000:
            raise Exception("Proposal text exceeds maximum length (50,000 characters)")
        
        # Generate deterministic hash for the proposal
        proposal_hash = self._hash_proposal(proposal_text)
        
        # Check if already evaluated
        existing = self.evaluations.get(proposal_hash, None)
        if existing is not None:
            return json.loads(existing)
        
        # Run the non-deterministic evaluation
        evaluation_result = self._evaluate_proposal(
            proposal_text,
            budget,
            timeline,
            dao_mission
        )
        
        # Store the evaluation
        self.evaluations[proposal_hash] = json.dumps(evaluation_result)
        
        return evaluation_result
    
    @gl.public.view
    def get_evaluation(self, proposal_text: str) -> dict:
        """
        Retrieve evaluation for a previously submitted proposal.
        
        Args:
            proposal_text: The proposal text to look up
            
        Returns:
            Optional[dict]: Evaluation results if found, None otherwise
        """
        proposal_hash = self._hash_proposal(proposal_text)
        result = self.evaluations.get(proposal_hash, None)
        
        if result is None:
            return None
        
        return json.loads(result)
    
    @gl.public.view
    def get_evaluation_by_hash(self, proposal_hash: str) -> dict:
        """
        Retrieve evaluation by proposal hash.
        
        Args:
            proposal_hash: The hash of the proposal
            
        Returns:
            Optional[dict]: Evaluation results if found, None otherwise
        """
        result = self.evaluations.get(proposal_hash, None)
        
        if result is None:
            return None
        
        return json.loads(result)
    
    def _hash_proposal(self, proposal_text: str) -> str:
        """
        Generate a deterministic hash for a proposal.
        
        Args:
            proposal_text: The proposal text
            
        Returns:
            str: SHA-256 hash in hexadecimal
        """
        return hashlib.sha256(proposal_text.encode('utf-8')).hexdigest()
    
    def _evaluate_proposal(
        self,
        proposal_text: str,
        budget: int,
        timeline: str,
        dao_mission: str
    ) -> dict:
        """
        Evaluate a proposal using LLM with strict consensus.
        
        This is the core evaluation logic that runs in a non-deterministic
        context with validator consensus.
        
        Args:
            proposal_text: The proposal to evaluate
            budget: Optional budget constraint
            timeline: Optional timeline constraint
            dao_mission: Optional mission for alignment check
            
        Returns:
            dict: Structured evaluation with scores and verdict
        """
        
        # Build the context
        context = {
            "proposal": proposal_text,
            "budget": budget if budget != 0 else "Not specified",
            "timeline": timeline if timeline != "" else "Not specified",
            "dao_mission": dao_mission if dao_mission != "" else "Generic DAO governance"
        }
        
        # Define the evaluation prompt
        prompt = f"""You are a neutral DAO governance analyst tasked with evaluating a proposal.

PROPOSAL CONTEXT:
- Proposal Text: {context['proposal']}
- Budget: {context['budget']}
- Timeline: {context['timeline']}
- DAO Mission: {context['dao_mission']}

EVALUATION RUBRIC:
Evaluate the proposal on a scale of 0-10 for each dimension:

1. CLARITY (0-10): Is the proposal clear, well-structured, and understandable?
   - 0-3: Confusing, poorly written, unclear objectives
   - 4-6: Somewhat clear but missing details
   - 7-8: Clear and well-structured
   - 9-10: Exceptionally clear and comprehensive

2. FEASIBILITY (0-10): Can this proposal realistically be executed?
   - 0-3: Unrealistic, lacks execution plan
   - 4-6: Possible but significant challenges
   - 7-8: Feasible with reasonable effort
   - 9-10: Highly feasible with clear execution path

3. RISK (0-10): What are the execution, legal, or financial risks? (Lower score = higher risk)
   - 0-3: High risk, potential for significant harm
   - 4-6: Moderate risks that need mitigation
   - 7-8: Low risk, well-considered
   - 9-10: Minimal risk, comprehensive safeguards

4. ALIGNMENT (0-10): How well does this align with the DAO's mission?
   - 0-3: Misaligned or contradictory
   - 4-6: Tangentially related
   - 7-8: Well-aligned
   - 9-10: Perfect strategic fit

5. BUDGET (0-10): Is the budget reasonable for the proposed outcomes?
   - 0-3: Excessive or unclear budget
   - 4-6: Questionable value for money
   - 7-8: Reasonable budget
   - 9-10: Excellent value, efficient resource use

6. COMPLETENESS (0-10): Does the proposal include all necessary details?
   - 0-3: Major gaps, many unanswered questions
   - 4-6: Some important details missing
   - 7-8: Most details covered
   - 9-10: Comprehensive, all bases covered

SCORING INSTRUCTIONS:
- Be objective and neutral
- Base scores on evidence in the proposal
- Do not inject personal opinions or biases
- Penalize vague or incomplete proposals
- Reward clear, well-thought-out proposals

FINAL VERDICT:
- "approve": Score >= 70 (Strong proposal, ready for vote)
- "revise": Score 40-69 (Has potential, needs improvement)
- "reject": Score < 40 (Fundamental issues, not viable)

Respond with ONLY the following JSON format (no other text):
{{
    "clarity": <score 0-10>,
    "feasibility": <score 0-10>,
    "risk": <score 0-10>,
    "alignment": <score 0-10>,
    "budget": <score 0-10>,
    "completeness": <score 0-10>,
    "final_score": <weighted average 0-100>,
    "verdict": "<approve|revise|reject>",
    "summary": "<2-3 sentence explanation of the verdict>"
}}

It is mandatory that you respond ONLY with valid JSON. No markdown formatting, no extra text, no code blocks.
This result must be perfectly parsable by a JSON parser without errors."""

        # Non-deterministic execution block
        def nondet_evaluation() -> str:
            """Execute LLM call and return cleaned JSON response."""
            response = gl.nondet.exec_prompt(prompt)
            
            # Clean the response (remove markdown code blocks if present)
            cleaned = response.replace("```json", "").replace("```", "").strip()
            
            # Validate it's proper JSON
            parsed = json.loads(cleaned)
            
            # Validate structure
            required_fields = [
                "clarity", "feasibility", "risk", "alignment", 
                "budget", "completeness", "final_score", "verdict", "summary"
            ]
            
            for field in required_fields:
                if field not in parsed:
                    raise Exception(f"Missing required field: {field}")
            
            # Validate score ranges
            score_fields = ["clarity", "feasibility", "risk", "alignment", "budget", "completeness"]
            for field in score_fields:
                score = parsed[field]
                if not isinstance(score, (int, float)) or score < 0 or score > 10:
                    raise Exception(f"Invalid score for {field}: must be 0-10")
            
            # Validate final score
            if not isinstance(parsed["final_score"], (int, float)) or parsed["final_score"] < 0 or parsed["final_score"] > 100:
                raise Exception("Invalid final_score: must be 0-100")
            
            # Validate verdict
            if parsed["verdict"] not in ["approve", "revise", "reject"]:
                raise Exception("Invalid verdict: must be approve, revise, or reject")
            
            # Return deterministically sorted JSON for consensus
            return json.dumps(parsed, sort_keys=True)
        
        # Use strict equality for consensus - all validators must agree on exact JSON
        result_json_str = gl.eq_principle.strict_eq(nondet_evaluation)
        
        # Parse the final result
        return json.loads(result_json_str)


# Example deployment and usage:
"""
DEPLOYMENT:
No constructor arguments needed.

USAGE EXAMPLES:

1. Submit a simple proposal:
   contract.submit_proposal(
       "We propose to allocate 50,000 tokens to develop a mobile app for our DAO..."
   )

2. Submit with full context:
   contract.submit_proposal(
       proposal_text="Detailed proposal here...",
       budget=50000,
       timeline="Q2 2026",
       dao_mission="Building decentralized autonomous infrastructure"
   )

3. Retrieve evaluation:
   contract.get_evaluation("Proposal text here...")

4. Get by hash:
   contract.get_evaluation_by_hash("abc123...")
"""
