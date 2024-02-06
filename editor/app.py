import urllib.parse

import streamlit as st

from components.flex import st_flex
from core.constants import OAUTH_CLIENT_ID
from core.constants import OAUTH_STATE
from core.constants import REDIRECT_URI
from core.query_params import get_project_timestamp
from core.state import CurrentProject
from core.state import get_user
from core.state import User
from utils import init_state
from views.splash import render_splash
from views.wizard import render_editor

st.set_page_config(page_title="Croissant Editor", page_icon="🥐", layout="wide")

init_state()

user = get_user()

if OAUTH_CLIENT_ID and not user:
    query_params = st.query_params
    state = query_params.get("state")
    if state and state[0] == OAUTH_STATE:
        code = query_params.get("code")
        if not code:
            st.stop()
        try:
            st.session_state[User] = User.connect(code)
            # Clear the cache to force retrieving the new user.
            get_user()
        except:
            raise
        finally:
            st.query_params = {}
    else:
        redirect_uri = urllib.parse.quote(REDIRECT_URI, safe="")
        client_id = urllib.parse.quote(OAUTH_CLIENT_ID, safe="")
        state = urllib.parse.quote(OAUTH_STATE, safe="")
        scope = urllib.parse.quote("openid profile", safe="")
        url = f"https://huggingface.co/oauth/authorize?response_type=code&redirect_uri={redirect_uri}&scope={scope}&client_id={client_id}&state={state}"
        st.header("Croissant Editor")
        st.link_button("🤗 Login with Hugging Face", url)
        st.stop()


def _back_to_menu():
    """Sends the user back to the menu."""
    st.query_params = {}
    init_state(force=True)


def _logout():
    """Logs the user out."""
    st.cache_data.clear()
    st.session_state[User] = None
    _back_to_menu()


timestamp = get_project_timestamp()

button_width = 73  # This is the best value for the current content of the buttons.
buttons_widths = []
if OAUTH_CLIENT_ID:
    buttons_widths.append(button_width)
if timestamp:
    buttons_widths.append(button_width)
widths = [200, sum(buttons_widths) + 10]  # 10 being the space between elements.

with st_flex(
    flex_direction="row",
    justify_content="space-between",
    align_items="center",
    widths=widths,
):
    st.header("Croissant Editor")
    if OAUTH_CLIENT_ID or timestamp:
        with st_flex(
            flex_direction="row",
            justify_content="space-between",
            widths=buttons_widths,
        ):
            if OAUTH_CLIENT_ID:
                st.button("Log out", on_click=_logout)
            if timestamp:
                st.button("Home", on_click=_back_to_menu)

should_display_editor = bool(st.session_state.get(CurrentProject))

if should_display_editor:
    render_editor()
else:
    render_splash()
