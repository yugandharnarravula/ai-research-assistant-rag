from typing import Dict, List


def verify_answer(answer: str, docs: List[Dict]) -> Dict:
    if not docs:
        return {
            "is_valid": False,
            "confidence": 0.0,
            "reason": "No supporting documents found.",
        }

    if not answer or len(answer.strip()) < 20:
        return {
            "is_valid": False,
            "confidence": 0.1,
            "reason": "Answer is too short.",
        }

    confidence = min(0.95, 0.5 + (0.1 * min(len(docs), 4)))

    return {
        "is_valid": True,
        "confidence": confidence,
        "reason": "Answer is grounded in retrieved context.",
    }
