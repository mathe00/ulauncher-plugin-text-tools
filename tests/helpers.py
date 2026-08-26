"""
Shared test helpers for the Text Tools extension test suite.

Provides:
  - A fake KeywordQueryEvent standing in for the Ulauncher event object
  - Introspection utilities for the action/item trees built by main.py

NOTE on get_description(): current Ulauncher versions require a `query`
argument for ResultItem.get_description(); reading the backing `_description`
attribute directly keeps tests independent of that API detail.
"""

from typing import Any


class FakeKeywordQueryEvent:
    """Stand-in for ulauncher KeywordQueryEvent exposing get_argument()."""

    def __init__(self, argument: str = ""):
        self._argument = argument

    def get_argument(self):
        return self._argument


def items_of(action) -> list[Any]:
    """Extract the rendered item list from a RenderResultListAction."""
    return list(action.result_list)


def single_item(action):
    """Assert the action renders exactly one item and return it."""
    items = items_of(action)
    assert len(items) == 1, f"Expected 1 item, got {len(items)}"
    return items[0]


def name_of(item) -> str:
    """An item's display name (mirrors get_name())."""
    return item._name


def desc_of(item) -> str:
    """An item's stored description text (see module NOTE)."""
    return item._description


def icon_of(item) -> Any:
    """An item's raw icon value (path string or pixbuf)."""
    return item._icon


def copy_text_of(item) -> str:
    """
    Extract the clipboard payload attached to an item.

    Returns None when the item has no CopyToClipboardAction (e.g. the
    empty-input prompt item whose on_enter is None).
    """
    if item._on_enter is None:
        return None
    assert hasattr(item._on_enter, "text"), (
        f"Expected a clipboard action, got {type(item._on_enter)}"
    )
    return item._on_enter.text
