from state import CurrentStep
import streamlit as st


def set_form_step(action, step=None):
    """Maintains the user's location within the wizard."""
    if action == "Next":
        st.session_state[CurrentStep] = min(3, st.session_state[CurrentStep] + 1)
    if action == "Back":
        st.session_state[CurrentStep] = max(1, st.session_state[CurrentStep] - 1)
    if action == "Jump" and step is not None:
        st.session_state[CurrentStep] = step


def render_side_buttons():
    def button_type(i: int) -> str:
        """Determines button color: red when user is on that given step."""
        return "primary" if st.session_state[CurrentStep] == i else "secondary"

    st.button(
        "Metadata",
        on_click=set_form_step,
        args=["Jump", 1],
        type=button_type(1),
        use_container_width=True,
    )
    st.button(
        "Files",
        on_click=set_form_step,
        args=["Jump", 2],
        type=button_type(2),
        use_container_width=True,
    )
    st.button(
        "RecordSets",
        on_click=set_form_step,
        args=["Jump", 3],
        type=button_type(3),
        use_container_width=True,
    )
