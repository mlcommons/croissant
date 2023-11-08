"""issues module."""

import dataclasses


class ValidationError(Exception):
    """Error during the validation of the format."""


class GenerationError(Exception):
    """Error during the generation of the dataset."""


@dataclasses.dataclass
class Context:
    """Context to identify an issue.

    This allows to add context to an issue by tracing it back:
    - within a given dataset,
    - within a given distribution,
    - within a given record set,
    - within a given field,
    - within a given sub field.
    """

    dataset_name: str | None = None
    distribution_name: str | None = None
    record_set_name: str | None = None
    field_name: str | None = None
    sub_field_name: str | None = None


@dataclasses.dataclass(frozen=True)
class Issues:
    """Issues during the validation of the format.

    Issues can either be errors (blocking) or warnings (informative).

    We use sets to represent errors and warnings to avoid repeated strings.
    """

    errors: set[str] = dataclasses.field(default_factory=set, hash=False)
    warnings: set[str] = dataclasses.field(default_factory=set, hash=False)

    def _wrap_in_context(self, context: Context | None, issue: str) -> str:
        if context is None:
            return issue
        local_context = []
        if context.dataset_name is not None:
            local_context.append(f"dataset({context.dataset_name})")
        if context.distribution_name is not None:
            local_context.append(f"distribution({context.distribution_name})")
        if context.record_set_name is not None:
            local_context.append(f"record_set({context.record_set_name})")
        if context.field_name is not None:
            local_context.append(f"field({context.field_name})")
        if context.sub_field_name is not None:
            local_context.append(f"sub_field({context.sub_field_name})")
        if not local_context:
            return issue
        return f"[{' > '.join(local_context)}] {issue}"

    def add_error(self, error: str, context: Context | None = None):
        """Mutates self.errors with a new error."""
        self.errors.add(self._wrap_in_context(context, error))

    def add_warning(self, warning: str, context: Context | None = None):
        """Mutates self.warnings with a new warning."""
        self.warnings.add(self._wrap_in_context(context, warning))

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
