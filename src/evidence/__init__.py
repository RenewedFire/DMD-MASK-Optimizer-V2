"""Evidence-driven detector evaluation."""

from src.evidence.evaluation import (
    DetectorOptions,
    EvaluationFrameResult,
    EvaluationReport,
    FailurePattern,
    analyze_failure_patterns,
    evaluate_evidence_export,
    optimize_detector_options,
)

__all__ = [
    "DetectorOptions",
    "EvaluationFrameResult",
    "EvaluationReport",
    "FailurePattern",
    "analyze_failure_patterns",
    "evaluate_evidence_export",
    "optimize_detector_options",
]
