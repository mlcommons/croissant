import os

import streamlit.components.v1 as components

from core.constants import OVERVIEW

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "tabs_component",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("tabs_component", path=build_dir)


def render_tabs(tabs: list[str], selected_tab: int, json: str | None, key=None):
    """Create a new instance of "tabs_component".

    Args:
        tabs: The tabs to render in the component.
        selected_tab: The selected tab.
        key: An optional key that uniquely identifies this component. If this is
            None, and the component's arguments are changed, the component will
            be re-mounted in the Streamlit frontend and lose its current state.

    Returns:
        The number of times the component's "Click Me" button has been clicked.
            (This is the value passed to `Streamlit.setComponentValue` on the
            frontend.)
    """
    component_value = _component_func(
        tabs=tabs,
        selected_tab=selected_tab,
        json=json,
        key=key,
        default=OVERVIEW,
    )
    return component_value
