"""Evidence-driven detector evaluation."""

from src.evidence.evaluation import (
    DetectorOptions,
    EvaluationFrameResult,
    EvaluationReport,
    FailurePattern,
    analyze_failure_patterns,
    evaluate_evidence_export,
    evaluate_evidence_export_with_layout_prior,
    evaluate_evidence_export_with_layout_prior_options,
    optimize_layout_prior_options,
    optimize_detector_options,
)
from src.evidence.learning import (
    LayoutPriorModel,
    LayoutPriorOptions,
    LearnedRegionTemplate,
    train_layout_prior_model,
)

__all__ = [
    "DetectorOptions",
    "EvaluationFrameResult",
    "EvaluationReport",
    "FailurePattern",
    "LayoutPriorModel",
    "LayoutPriorOptions",
    "LearnedRegionTemplate",
    "analyze_failure_patterns",
    "evaluate_evidence_export",
    "evaluate_evidence_export_with_layout_prior",
    "evaluate_evidence_export_with_layout_prior_options",
    "optimize_layout_prior_options",
    "optimize_detector_options",
    "train_layout_prior_model",
]
