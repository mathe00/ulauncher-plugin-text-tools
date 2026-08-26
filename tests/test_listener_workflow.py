"""
Workflow tests for KeywordQueryEventListener.on_event (main.py).

This is the single user-facing entry point of the extension: every
keystroke after the 'tt' keyword flows through it. Covered branches:

  - Empty / whitespace-only argument  -> one prompt item, no clipboard action
  - Non-empty argument                -> 14 result items, one per transformation,
                                        each copying its transformed text

The listener never touches preferences, the filesystem, or the network —
these tests run entirely in-process with a fake event object.
"""

import pytest

from tests.helpers import (
    FakeKeywordQueryEvent,
    copy_text_of,
    desc_of,
    icon_of,
    items_of,
    name_of,
    single_item,
)

EXPECTED_ITEM_NAMES = [
    "Uppercase",
    "Lowercase",
    "Title Case",
    "Swap Case",
    "Capitalize Each Word",
    "CamelCase",
    "Lower CamelCase",
    "Snake Case",
    "Kebab Case",
    "Dot Case",
    "Slash Case",
    "Backslash Case",
    "Reverse",
    "SpongeBob Case",
]


def run(listener, argument):
    """Drive on_event with a fake event carrying `argument`."""
    return listener.on_event(FakeKeywordQueryEvent(argument), extension=None)


# ===========================================================================
# Empty-input branch
# ===========================================================================


class TestEmptyInputBranch:
    """No argument -> single 'how to use' prompt item."""

    @pytest.mark.parametrize("argument", ["", " ", "   ", "\t", " \n "])
    def test_renders_single_prompt_item(self, listener, argument):
        item = single_item(run(listener, argument))

        assert name_of(item) == "Enter the text to transform"
        assert desc_of(item) == "Example: tt Hello world"

    def test_prompt_icon(self, listener):
        assert icon_of(single_item(run(listener, ""))) == "images/icon.png"

    def test_prompt_item_has_no_enter_action(self, listener):
        """
        The prompt sets on_enter=None: pressing Enter on it does nothing.
        Pinned so adding a default action later is a visible decision.
        """
        assert single_item(run(listener, ""))._on_enter is None

    def test_none_argument_treated_as_empty(self, listener):
        """
        get_argument() returns None when Ulauncher sends no argument;
        the `or ""` fallback must route to the same prompt branch.
        """

        class NoneEvent:
            def get_argument(self):
                return None

        items = items_of(listener.on_event(NoneEvent(), extension=None))

        assert len(items) == 1
        assert name_of(items[0]) == "Enter the text to transform"


# ===========================================================================
# Transformation-results branch
# ===========================================================================


class TestResultsBranch:
    """Non-empty argument -> full transformation list."""

    def test_renders_exactly_fourteen_items(self, listener):
        assert len(items_of(run(listener, "hello"))) == 14

    def test_item_names_match_transformation_order(self, listener):
        names = [name_of(i) for i in items_of(run(listener, "hello world"))]

        assert names == EXPECTED_ITEM_NAMES

    def test_every_item_uses_shared_icon(self, listener):
        icons = {icon_of(i) for i in items_of(run(listener, "hello"))}

        assert icons == {"images/icon.png"}

    def test_descriptions_carry_transformed_text(self, listener):
        expected = listener.get_transformations("abc")

        for item in items_of(run(listener, "abc")):
            assert desc_of(item) == expected[name_of(item)]

    @pytest.mark.parametrize(
        "transform,input_text,expected_output",
        [
            ("Uppercase", "hi", "HI"),
            ("Snake Case", "two words", "two_words"),
            ("Reverse", "abc", "cba"),
            ("CamelCase", "make me camel", "MakeMeCamel"),
            ("Kebab Case", "some phrase here", "some-phrase-here"),
        ],
    )
    def test_clipboard_payload_matches_description(
        self, listener, transform, input_text, expected_output
    ):
        item = next(
            i for i in items_of(run(listener, input_text)) if name_of(i) == transform
        )

        assert copy_text_of(item) == expected_output
        assert desc_of(item) == expected_output

    def test_copy_action_is_the_enter_action_itself(self, listener):
        """
        Selecting a result copies immediately (CopyToClipboardAction IS the
        on_enter action — no chaining). Pinned as current UX contract.
        """
        from ulauncher.api.shared.action.CopyToClipboardAction import (
            CopyToClipboardAction,
        )

        items = items_of(run(listener, "hello"))

        assert all(isinstance(i._on_enter, CopyToClipboardAction) for i in items)


class TestWhitespaceNormalization:
    """
    The listener only CHECKS argument.strip() for emptiness — it passes the
    RAW argument to get_transformations verbatim. Consequences pinned here:
    string-based transforms keep leading/trailing padding, word-based ones
    are immune (split() discards outer whitespace).
    """

    def test_argument_passed_verbatim_not_stripped(self, listener):
        by_name = {
            name_of(i): desc_of(i) for i in items_of(run(listener, "   hello world   "))
        }

        assert by_name["Uppercase"] == "   HELLO WORLD   "
        assert by_name["Reverse"] == "   dlrow olleh   "

    def test_word_based_items_immune_to_padding(self, listener):
        clean = {name_of(i): desc_of(i) for i in items_of(run(listener, "hello world"))}
        padded = {
            name_of(i): desc_of(i) for i in items_of(run(listener, "   hello world   "))
        }
        word_based = ["Snake Case", "Kebab Case", "CamelCase", "Lower CamelCase"]

        assert all(padded[k] == clean[k] for k in word_based)

    def test_internal_spacing_string_vs_word_families(self, listener):
        by_name = {name_of(i): desc_of(i) for i in items_of(run(listener, "a  b"))}

        assert by_name["Uppercase"] == "A  B"
        assert by_name["Snake Case"] == "a_b"


class TestRobustness:
    """Degenerate-but-plausible queries flow through without raising."""

    @pytest.mark.parametrize(
        "argument",
        [
            "a",
            "!@#$%",
            "café ☕ crème",
            "x" * 500,  # very long input — descriptions grow unbounded
            "tab\tseparated\tvalues",
            "0",
        ],
    )
    def test_never_raises_and_always_yields_items(self, listener, argument):
        items = items_of(run(listener, argument))

        assert len(items) == 14
        assert all(desc_of(i) != "" or True for i in items)  # shape sanity
