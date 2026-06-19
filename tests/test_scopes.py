from app import scope_utils


def test_parse_splits_on_whitespace() -> None:
    assert scope_utils.parse("read write") == {"read", "write"}


def test_parse_collapses_extra_whitespace() -> None:
    assert scope_utils.parse("  read   write\twrite ") == {"read", "write"}


def test_parse_none_is_empty() -> None:
    assert scope_utils.parse(None) == set()


def test_parse_empty_string_is_empty() -> None:
    assert scope_utils.parse("") == set()


def test_is_subset_true() -> None:
    assert scope_utils.is_subset("read", "read write") is True


def test_is_subset_equal() -> None:
    assert scope_utils.is_subset("read write", "write read") is True


def test_is_subset_empty_child_is_always_subset() -> None:
    assert scope_utils.is_subset("", "read") is True
    assert scope_utils.is_subset(None, None) is True


def test_is_subset_false() -> None:
    assert scope_utils.is_subset("read delete", "read write") is False


def test_check_in_configured_scopes_true() -> None:
    configured = {"read", "write"}
    assert scope_utils.check_in_configured_scopes(configured, "read") is True
    assert scope_utils.check_in_configured_scopes(configured, "write") is True
    assert scope_utils.check_in_configured_scopes(configured, "read write") is True
    assert scope_utils.check_in_configured_scopes(configured, None) is True
    assert scope_utils.check_in_configured_scopes(configured, "") is True


def test_check_in_configured_scopes_false() -> None:
    configured = {"read", "write"}
    assert scope_utils.check_in_configured_scopes(configured, "delete") is False
    assert scope_utils.check_in_configured_scopes(configured, "read delete") is False


def test_check_in_configured_scopes_empty_configured() -> None:
    configured: set[str] = set()
    assert scope_utils.check_in_configured_scopes(configured, "read") is False
    assert scope_utils.check_in_configured_scopes(configured, None) is True
    assert scope_utils.check_in_configured_scopes(configured, "") is True
