import json
from pathlib import Path

from services.generator import generate_answer
from services.reranker import rerank
from services.retriever import hybrid_search


def keyword_overlap(answer: str, keywords: list[str]) -> float:
    answer_lower = answer.lower()
    hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return hits / max(len(keywords), 1)


def run_eval() -> None:
    path = Path("evaluation/gold_questions.json")
    cases = json.loads(path.read_text())

    results = []
    for case in cases:
        docs = hybrid_search(case["question"], case["domain"])
        docs = rerank(case["question"], docs)
        response = generate_answer(case["question"], docs)
        score = keyword_overlap(response["answer"], case["expected_keywords"])

        results.append(
            {
                "question": case["question"],
                "domain": case["domain"],
                "score": score,
                "sources_found": len(response["sources"]),
            }
        )

    avg = sum(r["score"] for r in results) / max(len(results), 1)

    print("Evaluation results:")
    for r in results:
        print(r)

    print(f"\nAverage score: {avg:.2f}")


if __name__ == "__main__":
    run_eval()
