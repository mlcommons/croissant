import os

import streamlit.components.v1 as components

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "tree_component",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("tree_component", path=build_dir)


def render_tree(nodes, key=None):
    """Create a new instance of "tree_component".

    Args:
        nodes: The nodes to render in the tree. Nodes are dictionaries with keys `name`
            (unique identifier), `type` and `parent` (referencing another name).
        key: An optional key that uniquely identifies this component. If this is
            None, and the component's arguments are changed, the component will
            be re-mounted in the Streamlit frontend and lose its current state.

    Returns:
        The number of times the component's "Click Me" button has been clicked.
            (This is the value passed to `Streamlit.setComponentValue` on the
            frontend.)
    """
    component_value = _component_func(nodes=nodes, key=key, default=0)
    return component_value
