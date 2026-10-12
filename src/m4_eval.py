from __future__ import annotations

"""Module 4: RAGAS Evaluation — 4 metrics + evaluator_models metadata."""

import json
import math
import os
import sys
from dataclasses import dataclass

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TEST_SET_PATH

EVALUATOR_LLM_MODEL = "gpt-4o-mini"
EVALUATOR_EMBEDDING_MODEL = "text-embedding-3-small"


@dataclass
class EvalResult:
    question: str
    answer: str
    contexts: list[str]
    ground_truth: str
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float


def load_test_set(path: str = TEST_SET_PATH) -> list[dict]:
    """Load test set from JSON."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _clamp_score(val: object) -> float | None:
    try:
        v = float(val)
        if not math.isfinite(v):
            return None
        return min(1.0, max(0.0, v))
    except Exception:
        return None


def evaluate_ragas(questions: list[str], answers: list[str],
                   contexts: list[list[str]], ground_truths: list[str]) -> dict:
    """Run RAGAS evaluation and report actual evaluator models in metadata."""
    from datasets import Dataset
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from ragas import evaluate
    from ragas.run_config import RunConfig
    try:
        from ragas.metrics.collections import faithfulness, answer_relevancy, context_precision, context_recall
    except ImportError:
        from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall

    eval_llm = ChatOpenAI(model=EVALUATOR_LLM_MODEL, temperature=0)
    eval_embeddings = OpenAIEmbeddings(model=EVALUATOR_EMBEDDING_MODEL)
    metrics_list = [faithfulness, answer_relevancy, context_precision, context_recall]
    metric_names = ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
    run_cfg = RunConfig(max_retries=5, max_wait=60, max_workers=8)

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths,
    })
    result = evaluate(
        dataset,
        metrics=metrics_list,
        llm=eval_llm,
        embeddings=eval_embeddings,
        run_config=run_cfg,
        raise_exceptions=False,
    )
    df = result.to_pandas()

    per_question: list[EvalResult] = []
    for idx, row in df.iterrows():
        scores: dict[str, float] = {}
        missing_metrics = []
        for m_obj, m_name in zip(metrics_list, metric_names):
            s = _clamp_score(row.get(m_name))
            if s is None:
                missing_metrics.append((m_obj, m_name))
            else:
                scores[m_name] = s

        # Retry single question if any metric returned NaN due to transient API parse error
        if missing_metrics:
            single_ds = Dataset.from_dict({
                "question": [questions[idx]],
                "answer": [answers[idx]],
                "contexts": [contexts[idx]],
                "ground_truth": [ground_truths[idx]],
            })
            for _attempt in range(3):
                still_missing = [(m_obj, m_name) for m_obj, m_name in missing_metrics if m_name not in scores]
                if not still_missing:
                    break
                retry_res = evaluate(
                    single_ds,
                    metrics=[m_obj for m_obj, _ in still_missing],
                    llm=eval_llm,
                    embeddings=eval_embeddings,
                    run_config=RunConfig(max_retries=5, max_wait=60, max_workers=2),
                    raise_exceptions=False,
                )
                retry_df = retry_res.to_pandas()
                if len(retry_df) > 0:
                    r_row = retry_df.iloc[0]
                    for _, m_name in still_missing:
                        s = _clamp_score(r_row.get(m_name))
                        if s is not None:
                            scores[m_name] = s

        for m_name in metric_names:
            if m_name not in scores:
                raise ValueError(f"RAGAS failed to produce finite score for {m_name} at question index {idx}")

        per_question.append(EvalResult(
            question=questions[idx],
            answer=answers[idx],
            contexts=list(contexts[idx]),
            ground_truth=ground_truths[idx],
            faithfulness=scores["faithfulness"],
            answer_relevancy=scores["answer_relevancy"],
            context_precision=scores["context_precision"],
            context_recall=scores["context_recall"],
        ))

    def _mean_val(metric_name: str) -> float:
        vals = [getattr(pq, metric_name) for pq in per_question]
        return float(sum(vals) / len(vals)) if vals else 0.0

    return {
        "faithfulness": _mean_val("faithfulness"),
        "answer_relevancy": _mean_val("answer_relevancy"),
        "context_precision": _mean_val("context_precision"),
        "context_recall": _mean_val("context_recall"),
        "per_question": per_question,
        "metadata": {
            "evaluator_models": [EVALUATOR_LLM_MODEL, EVALUATOR_EMBEDDING_MODEL],
        },
    }
