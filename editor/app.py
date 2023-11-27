import urllib.parse

import streamlit as st

from core.constants import OAUTH_CLIENT_ID
from core.constants import OAUTH_STATE
from core.constants import REDIRECT_URI
from core.state import CurrentStep
from core.state import get_cached_user
from core.state import User
from utils import init_state
from views.splash import render_splash
from views.wizard import render_editor

st.set_page_config(page_title="Croissant Editor", page_icon="🥐", layout="wide")
col1, col2, col3 = st.columns([10, 1, 1])
col1.header("Croissant Editor")

init_state()

user = get_cached_user()

if OAUTH_CLIENT_ID and not user:
    query_params = st.experimental_get_query_params()
    state = query_params.get("state")
    if state and state[0] == OAUTH_STATE:
        code = query_params.get("code")
        if not code:
            st.stop()
        try:
            st.session_state[User] = User.connect(code)
            # Clear the cache to force retrieving the new user.
            get_cached_user.clear()
            get_cached_user()
        except:
            raise
        finally:
            st.experimental_set_query_params()
    else:
        redirect_uri = urllib.parse.quote(REDIRECT_URI, safe="")
        client_id = urllib.parse.quote(OAUTH_CLIENT_ID, safe="")
        state = urllib.parse.quote(OAUTH_STATE, safe="")
        scope = urllib.parse.quote("openid profile", safe="")
        url = f"https://huggingface.co/oauth/authorize?response_type=code&redirect_uri={redirect_uri}&scope={scope}&client_id={client_id}&state={state}"
        st.link_button("🤗 Login with Hugging Face", url)
        st.stop()


def _back_to_menu():
    """Sends the user back to the menu."""
    init_state(force=True)
    st.experimental_set_query_params()


def _logout():
    """Logs the user out."""
    st.cache_data.clear()


if OAUTH_CLIENT_ID:
    col2.write("\n")  # Vertical box to shift the lgout menu
    col2.button("Log out", on_click=_logout)


if st.session_state[CurrentStep] != CurrentStep.splash:
    col3.write("\n")  # Vertical box to shift the button menu
    col3.button("Menu", on_click=_back_to_menu)


if st.session_state[CurrentStep] == CurrentStep.splash:
    render_splash()
elif st.session_state[CurrentStep] == CurrentStep.editor:
    render_editor()
else:
    st.warning("invalid unhandled app state")
