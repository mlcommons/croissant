import contextlib

import streamlit as st
import streamlit.components.v1 as components


@contextlib.contextmanager
def st_flex(
    flex_direction="null",
    justify_content="null",
    align_items="null",
    flex="null",
    widths=None,
):
    """[flex](https://developer.mozilla.org/en-US/docs/Web/CSS/flex) for Streamlit.

    Warning: This custom component uses a lot of heuristics. But styling flex is
    important in CSS and missing from Streamlit. st.columns does a poor job at
    horizontally aligning elements.

    Args:
        flex_direction: https://developer.mozilla.org/en-US/docs/Web/CSS/flex-direction
        justify_content:
            https://developer.mozilla.org/en-US/docs/Web/CSS/justify-content
        align_items: https://developer.mozilla.org/en-US/docs/Web/CSS/align-items
        flex: https://developer.mozilla.org/en-US/docs/Web/CSS/flex
        widths: An array containing the minimal widths of all elements. This somewhat
            defeats the purpose of flex, but Streamlit forces the width of elements,
            which is why forcing this parameter is unfortunately needed.
    """
    placeholder = st.empty()
    with placeholder.container():
        placeholder = st.empty()
        with placeholder.container():
            yield
        components.html(
            f"""
            <script>
            window.frameElement.style.display = 'none';
            // Get the current script node
            const frameElement = window.frameElement.parentElement;

            // Get the parent element
            const parentElement = frameElement.parentElement;

            // Change container
            const container = parentElement.firstChild.firstChild;
            container.style.display = 'flex';
            container.style.flexDirection = '{flex_direction}';
            container.style.justifyContent = '{justify_content}';
            container.style.flex = '{flex}';
            container.style.alignItems = '{align_items}';
            container.width = '';
            container.className = '';

            // Change children
            let i = 0;
            for (const child of container.children) {{
              child.style.width = `${{{widths}?.[i] || 60}}px`;
              child.className = '';
              i += 1;
            }}
            </script>""",
        )
