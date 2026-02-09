# { "Depends": "py-genlayer:latest" }

from genlayer import *
import json
import hashlib
import typing


class DaoProposalEvaluator(gl.Contract):
    """
    Deterministic, LLM-powered DAO proposal evaluation contract.
    """

    evaluations: TreeMap[str, str]

    def __init__(self):
        # TreeMap is auto-initialized by GenLayer
        pass

    # -----------------------------
    # Internal helpers
    # -----------------------------

    def _hash_proposal(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _safe_parse_json(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except Exception:
            return {
                "final_score": 0,
                "verdict": "reject",
                "scores": {
                    "clarity": 0,
                    "feasibility": 0,
                    "risk": 0,
                    "alignment": 0,
                    "budget": 0,
                    "completeness": 0
                },
                "summary": "Invalid or unparsable model output"
            }

    # -----------------------------
    # Public write method
    # -----------------------------

    @gl.public.write
    def submit_proposal(self, proposal_text: str) -> dict[str, typing.Any]:
        """
        Evaluates a DAO proposal using deterministic LLM consensus.
        """

        proposal_hash = self._hash_proposal(proposal_text)

        if proposal_hash in self.evaluations:
            return self._safe_parse_json(self.evaluations[proposal_hash])

        prompt = (
            "You are a neutral DAO governance analyst.\n"
            "Evaluate the following proposal strictly using the rubric.\n\n"
            "Rubric (0-10 each):\n"
            "- clarity\n"
            "- feasibility\n"
            "- risk\n"
            "- alignment\n"
            "- budget\n"
            "- completeness\n\n"
            "Proposal:\n"
            f"{proposal_text}\n\n"
            "Respond ONLY with valid JSON in this format:\n"
            "{\n"
            '  "final_score": int,\n'
            '  "verdict": "approve" | "revise" | "reject",\n'
            '  "scores": {\n'
            '    "clarity": int,\n'
            '    "feasibility": int,\n'
            '    "risk": int,\n'
            '    "alignment": int,\n'
            '    "budget": int,\n'
            '    "completeness": int\n'
            "  },\n"
            '  "summary": str\n'
            "}\n"
            "No markdown. No extra text."
        )

        def nondet_eval() -> str:
            try:
                res = gl.nondet.exec_prompt(prompt)
                return res.replace("```json", "").replace("```", "").strip()
            except Exception:
                return "{}"

        raw_result = gl.eq_principle.strict_eq(nondet_eval)
        parsed = self._safe_parse_json(raw_result)

        self.evaluations[proposal_hash] = json.dumps(parsed)

        return parsed

    # -----------------------------
    # Public view methods
    # -----------------------------

    @gl.public.view
    def get_evaluation(self, proposal_hash: str) -> dict[str, typing.Any]:
        if proposal_hash not in self.evaluations:
            return {}
        return self._safe_parse_json(self.evaluations[proposal_hash])

    @gl.public.view
    def has_evaluation(self, proposal_hash: str) -> bool:
        return proposal_hash in self.evaluations
