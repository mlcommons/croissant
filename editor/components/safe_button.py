import streamlit as st

HAS_CONFIRMED = "SAFELY_UPDATE"


def handle_on_click(on_click):
    """Handles on_click by waiting for the confirmation."""
    if st.session_state.get(HAS_CONFIRMED):
        return on_click
    else:

        def toggle_has_confirmed(*args, **kwargs):
            del args, kwargs  # unused.
            st.session_state[HAS_CONFIRMED] = not st.session_state.get(HAS_CONFIRMED)

        return toggle_has_confirmed


def button_with_confirmation(
    label: str,
    key: str = None,
    on_click=None,
    args=None,
    kwargs=None,
):
    """Implements a safe button that asks for confirmation before executing on_click."""
    st.button(
        label,
        on_click=handle_on_click(on_click),
        args=args,
        kwargs=kwargs,
        key=key,
        type="secondary",
    )
    if st.session_state.get(HAS_CONFIRMED):
        st.error(f"Do you really want to {label.lower()}? Click again to confirm.")
