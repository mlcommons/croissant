"""issues module."""

import contextlib
import dataclasses


class ValidationError(Exception):
    """Error during the validation of the format."""


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
    """
    Issues during the validation of the format.

    Issues can either be errors (blocking) or warnings (informative).

    We use sets to represent errors and warnings to avoid repeated strings.
    """

    errors: set[str] = dataclasses.field(default_factory=set, hash=False)
    warnings: set[str] = dataclasses.field(default_factory=set, hash=False)
    _local_context: Context = dataclasses.field(default_factory=Context, hash=False)

    def _wrap_in_local_context(self, issue: str) -> str:
        local_context = []
        if self._local_context.dataset_name is not None:
            local_context.append(f"dataset({self._local_context.dataset_name})")
        if self._local_context.distribution_name is not None:
            local_context.append(
                f"distribution({self._local_context.distribution_name})"
            )
        if self._local_context.record_set_name is not None:
            local_context.append(f"record_set({self._local_context.record_set_name})")
        if self._local_context.field_name is not None:
            local_context.append(f"field({self._local_context.field_name})")
        if self._local_context.sub_field_name is not None:
            local_context.append(f"sub_field({self._local_context.sub_field_name})")
        if not local_context:
            return issue
        return f"[{' > '.join(local_context)}] {issue}"

    def add_error(self, error: str):
        """Mutates self.errors with a new error."""
        self.errors.add(self._wrap_in_local_context(error))

    def add_warning(self, warning: str):
        """Mutates self.warnings with a new warning."""
        self.warnings.add(self._wrap_in_local_context(warning))

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

    @contextlib.contextmanager
    def context(
        self,
        *,
        dataset_name: str | None = None,
        distribution_name: str | None = None,
        record_set_name: str | None = None,
        field_name: str | None = None,
        sub_field_name: str | None = None,
    ):
        """Context manager to add a string context to each error/warning.

        Usage:
            This prints the error "[dataset(abc)] xyz":
            ```
            with issues.context(dataset_id=abc"):
                issues.add_error("xyz")
            ```
        """
        tmp_dataset_name = self._local_context.dataset_name
        tmp_distribution_name = self._local_context.distribution_name
        tmp_record_set_name = self._local_context.record_set_name
        tmp_field_name = self._local_context.field_name
        tmp_sub_field_name = self._local_context.sub_field_name

        self._local_context.dataset_name = (
            dataset_name if dataset_name is not None else tmp_dataset_name
        )
        self._local_context.distribution_name = (
            distribution_name
            if distribution_name is not None
            else tmp_distribution_name
        )
        self._local_context.record_set_name = (
            record_set_name if record_set_name is not None else tmp_record_set_name
        )
        self._local_context.field_name = (
            field_name if field_name is not None else tmp_field_name
        )
        self._local_context.sub_field_name = (
            sub_field_name if sub_field_name is not None else tmp_sub_field_name
        )

        yield

        self._local_context.dataset_name = tmp_dataset_name
        self._local_context.distribution_name = tmp_distribution_name
        self._local_context.record_set_name = tmp_record_set_name
        self._local_context.field_name = tmp_field_name
        self._local_context.sub_field_name = tmp_sub_field_name
