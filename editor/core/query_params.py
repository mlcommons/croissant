"""Module to manipulate query params."""

from typing import Any

import streamlit as st

from core.state import CurrentProject
from core.state import RecordSet


class QueryParams:
    """Possible URL query params."""

    OPEN_PROJECT = "project"
    OPEN_RECORD_SET = "recordSet"


def _has_query_params() -> bool:
    """Returns whether `query_params` is available, which depends on the streamlit
    version. If not, st.experimental_get_query_params() and
    st.experimental_set_query_params() should be used."""
    return hasattr(st, "query_params")


def _get_query_param(name: str) -> str | None:
    """Gets query param with the name `name`."""
    if _has_query_params():
        param = st.query_params.get_all(name)
    else:
        params = st.experimental_get_query_params()
        if not name in params:
            return None
        param = params[name]

    if isinstance(param, list) and len(param) > 0:
        return param[0]
    return None


def _set_query_param(param: str, new_value: str) -> str | None:
    """Sets query param with the name `name` to `new_value`."""
    if _has_query_params():
        params = st.query_params
        if params.get_all(param) == [new_value]:
            # The value already exists in the query params.
            return
        params[param] = new_value
    else:
        params = st.experimental_get_query_params()
        if params.get(param) == [new_value]:
            # The value already exists in the query params.
            return
        new_params = {k: v for k, v in params.items() if k != param}
        new_params[param] = new_value
        st.experimental_set_query_params(**new_params)


def is_record_set_expanded(record_set: RecordSet) -> bool:
    open_record_set_name = _get_query_param(QueryParams.OPEN_RECORD_SET)
    if open_record_set_name:
        return open_record_set_name == record_set.name
    return False


def expand_record_set(record_set: RecordSet) -> None:
    _set_query_param(QueryParams.OPEN_RECORD_SET, record_set.name)


def get_project_timestamp() -> str | None:
    return _get_query_param(QueryParams.OPEN_PROJECT)


def get_state() -> str | None:
    return _get_query_param("state")


def set_project(project: CurrentProject):
    _set_query_param(QueryParams.OPEN_PROJECT, project.path.name)


def clear_query_params():
    """Clears query params."""
    if _has_query_params():
        st.query_params.clear()
    else:
        st.experimental_set_query_params()
