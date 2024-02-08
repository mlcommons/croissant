"""Module to manipulate query params."""

from typing import Any

import streamlit as st

from core.state import CurrentProject
from core.state import RecordSet


class QueryParams:
    """Possible URL query params."""

    OPEN_PROJECT = "project"
    OPEN_RECORD_SET = "recordSet"


def _get_query_param(params: dict[str, Any], name: str) -> str | None:
    """Gets query param with the name `name`."""
    if name in params:
        param = params[name]
        if isinstance(param, list) and len(param) > 0:
            return param[0]
    return None


def _set_query_param(param: str, new_value: str) -> str | None:
    params = st.query_params
    if params.get(param) == [new_value]:
        # The value already exists in the query params.
        return
    new_params = {k: v for k, v in params.items() if k != param}
    new_params[param] = new_value
    st.query_params = new_params


def is_record_set_expanded(record_set: RecordSet) -> bool:
    params = st.query_params
    open_record_set_name = _get_query_param(params, QueryParams.OPEN_RECORD_SET)
    if open_record_set_name:
        return open_record_set_name == record_set.name
    return False


def expand_record_set(record_set: RecordSet) -> None:
    _set_query_param(QueryParams.OPEN_RECORD_SET, record_set.name)


def get_project_timestamp() -> str | None:
    params = st.query_params
    return _get_query_param(params, QueryParams.OPEN_PROJECT)


def set_project(project: CurrentProject):
    _set_query_param(QueryParams.OPEN_PROJECT, project.path.name)
