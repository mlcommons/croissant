import contextlib
import dataclasses
from typing import List, Union


class ValidationError(Exception):
    """Error during the validation of the format."""


@dataclasses.dataclass
class Issues:
    """
    Issues during the validation of the format.

    Issues can either be errors (blocking) or warnings (informative).
    """

    errors: List[str] = dataclasses.field(default_factory=list)
    warnings: List[str] = dataclasses.field(default_factory=list)
    _local_context: Union[str, None] = None

    def _wrap_in_local_context(self, issue: str) -> str:
        if self._local_context is None:
            return issue
        return f"[{self._local_context}] {issue}"

    def add_error(self, error: str):
        """Mutates self.errors with a new error."""
        self.errors.append(self._wrap_in_local_context(error))

    def add_warning(self, warning: str):
        """Mutates self.warnings with a new warning."""
        self.warnings.append(self._wrap_in_local_context(warning))

    def report(self) -> str:
        """Reports errors and warnings in a string."""
        message = ""
        for issues, issue_type in [
            (self.errors, "error(s)"),
            (self.warnings, "warning(s)"),
        ]:
            num_issues = len(issues)
            if num_issues:
                message += f"Found the following {len(issues)} {issue_type} during the validation:\n"
                for issue in issues:
                    message += f"  -  {issue}\n"
        return message.strip()

    @contextlib.contextmanager
    def context(self, local_context: str):
        """Context manager to add a string context to each error/warning.

        Usage:
            This prints the error "[dataset_abc] xyz":
            ```
            with issues.context("dataset_abc"):
                issues.add_error("xyz")
            ```
        """
        self._local_context = local_context
        yield
        self._local_context = None
