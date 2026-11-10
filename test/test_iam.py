import pytest

from src.auth.iam import (
    AuthenticationError,
    ROLE_PERMISSIONS,
    _password_hash,
    _validate_account,
    _verify_password,
)


def test_password_hash_is_salted_and_verifiable():
    first = _password_hash("correct-horse-battery")
    second = _password_hash("correct-horse-battery")

    assert first != second
    assert _verify_password("correct-horse-battery", first)
    assert not _verify_password("incorrect-password", first)


def test_password_policy_requires_twelve_characters():
    with pytest.raises(AuthenticationError, match="12 characters"):
        _password_hash("short")


def test_removed_roles_are_rejected():
    with pytest.raises(AuthenticationError, match="valid role"):
        _validate_account("team.lead", "lead@example.com", "Manager")


def test_account_identifiers_are_normalized():
    assert _validate_account(
        "  Team.Lead ", " Lead@Example.com ", "HR"
    ) == ("team.lead", "lead@example.com")


def test_role_permissions_match_least_privilege_policy():
    assert "manage_users" in ROLE_PERMISSIONS["Admin"]
    assert "manage_employees" in ROLE_PERMISSIONS["HR"]
    assert "manage_users" not in ROLE_PERMISSIONS["HR"]
    assert ROLE_PERMISSIONS["Executive"] == frozenset()
    assert set(ROLE_PERMISSIONS) == {"Admin", "HR", "Executive"}
    assert "Manager" not in ROLE_PERMISSIONS
    assert "Viewer" not in ROLE_PERMISSIONS
