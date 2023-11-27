"""Module to manipulate query params."""

from typing import Any

import streamlit as st

from core.state import RecordSet


class QueryParams:
    """Possible URL query params."""

    OPEN_RECORD_SET = "recordSet"
    OPEN_TAB = "tab"


def _get_query_param(params: dict[str, Any], name: str) -> str | None:
    """Gets query param with the name `name`."""
    if name in params:
        param = params[name]
        if isinstance(param, list) and len(param) > 0:
            return param[0]
    return None


def go_to_tab(tabs: list[str]):
    params = st.experimental_get_query_params()
    if QueryParams.OPEN_TAB in params:
        tab = params[QueryParams.OPEN_TAB][0]
        if tab in tabs:
            index = tabs.index(tab)
            tab_id = f"tabs-bui1-tab-{index}"
            # Click on the tab.
            js = f"""
                <script>
                    const tab = window.parent.document.getElementById('{tab_id}');
                    tab.click();
                </script>
            """
            st.components.v1.html(js)


def is_record_set_expanded(record_set: RecordSet):
    params = st.experimental_get_query_params()
    open_record_set_name = _get_query_param(params, QueryParams.OPEN_RECORD_SET)
    if open_record_set_name:
        return open_record_set_name == record_set.name
    return False


def make_record_set_expanded(record_set: RecordSet):
    params = st.experimental_get_query_params()
    new_params = {k: v for k, v in params.items() if k != QueryParams.OPEN_RECORD_SET}
    new_params[QueryParams.OPEN_RECORD_SET] = record_set.name
    st.experimental_set_query_params(**new_params)
