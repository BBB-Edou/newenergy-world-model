"""Backward-compatible verification imports."""

from .engine import VerificationAgent
from .schema import VerificationIssue, VerificationResult

VerificationService = VerificationAgent
PlaceholderVerificationService = VerificationAgent

__all__ = [
    "PlaceholderVerificationService",
    "VerificationAgent",
    "VerificationIssue",
    "VerificationResult",
    "VerificationService",
]