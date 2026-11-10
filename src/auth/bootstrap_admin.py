"""Create the first administrator account and the IAM table."""

from getpass import getpass

from src.auth.iam import AuthenticationError, bootstrap_admin


def main() -> int:
    print("Create the first Employee Analytics administrator.")
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass("Password (at least 12 characters): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        print("Passwords do not match.")
        return 1
    try:
        user_id = bootstrap_admin(username, email, password)
    except AuthenticationError as err:
        print(f"IAM setup failed: {err}")
        return 1
    print(f"Administrator account created (user ID {user_id}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
