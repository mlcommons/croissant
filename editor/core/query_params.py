"""Module to manipulate query params."""

from typing import Any

import streamlit as st

from core.constants import TABS
from core.state import CurrentProject
from core.state import RecordSet


class QueryParams:
    """Possible URL query params."""

    OPEN_PROJECT = "project"
    OPEN_RECORD_SET = "recordSet"
    OPEN_TAB = "tab"


def _get_query_param(params: dict[str, Any], name: str) -> str | None:
    """Gets query param with the name `name`."""
    if name in params:
        param = params[name]
        if isinstance(param, list) and len(param) > 0:
            return param[0]
    return None


def _set_query_param(param: str, new_value: str) -> str | None:
    params = st.experimental_get_query_params()
    new_params = {k: v for k, v in params.items() if k != param}
    new_params[param] = new_value
    st.experimental_set_query_params(**new_params)


def go_to_tab(tabs: list[str]):
    params = st.experimental_get_query_params()
    if QueryParams.OPEN_TAB in params:
        try:
            tab = int(params[QueryParams.OPEN_TAB][0])
            if 0 <= tab and tab < len(tabs):
                tab_id = f"tabs-bui3-tab-{tab}"
                # Click on the tab.
                js = f"""
                    <script>
                        const tab = window.parent.document.getElementById('{tab_id}');
                        tab.click();
                    </script>
                """
                st.components.v1.html(js)
        except ValueError:
            pass


def set_tab(tab: str):
    if tab not in TABS:
        return
    index = TABS.index(tab)
    _set_query_param(QueryParams.OPEN_TAB, index)


def is_record_set_expanded(record_set: RecordSet) -> bool:
    params = st.experimental_get_query_params()
    open_record_set_name = _get_query_param(params, QueryParams.OPEN_RECORD_SET)
    if open_record_set_name:
        return open_record_set_name == record_set.name
    return False


def expand_record_set(record_set: RecordSet) -> None:
    _set_query_param(QueryParams.OPEN_RECORD_SET, record_set.name)


def get_project_timestamp() -> str | None:
    params = st.experimental_get_query_params()
    return _get_query_param(params, QueryParams.OPEN_PROJECT)


def set_project(project: CurrentProject):
    _set_query_param(QueryParams.OPEN_PROJECT, project.path.name)
