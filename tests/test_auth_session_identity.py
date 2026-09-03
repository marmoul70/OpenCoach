from opencoach.authentication.auth import (
    create_session_token,
    read_session_identity,
    verify_session_token,
)


USER_ID = (
    "11111111-1111-1111-1111-111111111111"
)


def test_session_token_contains_user_id():
    token, _ = create_session_token(
        USER_ID,
    )

    identity = read_session_identity(
        token,
    )

    assert identity is not None
    assert identity.user_id == USER_ID
    assert verify_session_token(
        token,
    )


def test_legacy_session_is_rejected():
    assert (
        read_session_identity(
            "123.test.signature"
        )
        is None
    )
