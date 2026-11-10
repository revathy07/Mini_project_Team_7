"""Streamlit session helpers and role permission checks."""

import time

import streamlit as st

from src.auth.iam import AuthenticationError, create_auth_schema, get_active_user

SESSION_TTL_SECONDS = 8 * 60 * 60


@st.cache_resource
def initialize_iam():
    create_auth_schema()


def current_user():
    user_id = st.session_state.get("iam_user_id")
    signed_in_at = st.session_state.get("iam_signed_in_at")
    if not user_id or not signed_in_at:
        return None
    if time.time() - signed_in_at > SESSION_TTL_SECONDS:
        logout()
        return None
    user = get_active_user(user_id)
    if user is None:
        logout()
    return user


def logout():
    st.session_state.clear()


def can(user, permission: str) -> bool:
    if user is None:
        return False
    from src.auth.iam import ROLE_PERMISSIONS

    return permission in ROLE_PERMISSIONS.get(user["role"], ())


def require_permission(permission: str):
    user = current_user()
    if not user or not can(user, permission):
        st.error("You do not have permission to access this feature.")
        st.stop()
    return user


def login(username: str, password: str) -> bool:
    from src.auth.iam import authenticate

    user = authenticate(username, password)
    if user is None:
        return False
    st.session_state["iam_user_id"] = user["user_id"]
    st.session_state["iam_signed_in_at"] = time.time()
    return True


__all__ = [
    "AuthenticationError", "can", "current_user", "login", "logout",
    "require_permission",
]
