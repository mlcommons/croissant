"""issues module."""

import dataclasses
from typing import Any


class ValidationError(Exception):
    """Error during the validation of the format."""


class GenerationError(Exception):
    """Error during the generation of the dataset."""


@dataclasses.dataclass(frozen=True)
class Issues:
    """Issues during the validation of the format.

    Issues can either be errors (blocking) or warnings (informative).

    We use sets to represent errors and warnings to avoid repeated strings.
    """

    _errors: set[tuple[str, Any]] = dataclasses.field(default_factory=set, hash=False)
    _warnings: set[tuple[str, Any]] = dataclasses.field(default_factory=set, hash=False)

    def _wrap_in_context(self, context: str | None, issue: str) -> str:
        if context is None:
            return issue
        return f"[{context}] {issue}"

    def add_error(self, error: str, node: Any = None):
        """Mutates self.errors with a new error."""
        self._errors.add((error, node))

    def add_warning(self, warning: str, node: Any = None):
        """Mutates self.warnings with a new warning."""
        self._warnings.add((warning, node))

    @property
    def errors(self) -> set[str]:
        """Outputs errors as a set of human-readable strings."""
        errors = set()
        for error, node in self._errors:
            if get_issue_context := getattr(node, "get_issue_context", None):
                if callable(get_issue_context):
                    errors.add(f"[{get_issue_context()}] {error}")
                    continue
            errors.add(error)
        return errors

    @property
    def warnings(self) -> set[str]:
        """Outputs warnings as a set of human-readable strings."""
        warnings = set()
        for error, node in self._warnings:
            if get_issue_context := getattr(node, "get_issue_context", None):
                if callable(get_issue_context):
                    warnings.add(f"[{get_issue_context()}] {error}")
                    continue
            warnings.add(error)
        return warnings

    def report(self) -> str:
        """Reports errors and warnings in a string."""
        message = ""
        # Sort before printing because sets are not ordered.
        for issues, issue_type in [
            (sorted(self.errors), "error(s)"),
            (sorted(self.warnings), "warning(s)"),
        ]:
            num_issues = len(issues)
            if num_issues:
                message += (
                    f"Found the following {len(issues)} {issue_type} during the"
                    " validation:\n"
                )
                for issue in issues:
                    message += f"  -  {issue}\n"
        return message.strip()
