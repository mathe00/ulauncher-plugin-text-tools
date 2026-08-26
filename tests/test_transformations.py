"""
Tests for the core text transformation logic
(main.KeywordQueryEventListener.get_transformations).

This is the entire value of the extension: 14 named transformations
returned as an insertion-ordered dict. Coverage strategy:

  - One happy-path class per transformation (exact expected outputs)
  - Edge-input classes: single word, extra whitespace, punctuation,
    apostrophes, digits, unicode, empty/whitespace-only input
  - Quirk documentation: str.title() apostrophe artifact, punctuation
    retention in CamelCase, SpongeBob starting uppercase, string-based
    transforms preserving whitespace while word-based ones collapse it
  - Structural invariants: exact key order, key set stability, count

All expectations were verified against the real implementation; quirks
are pinned deliberately so any behavior change is a conscious decision.
"""

from typing import ClassVar

import pytest

# Canonical input used across several test classes
CANONICAL = "hello world"

EXPECTED_ORDER = [
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


# ===========================================================================
# Per-transformation happy paths (canonical two-word input)
# ===========================================================================


class TestUppercase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Uppercase"] == "HELLO WORLD"

    @pytest.mark.parametrize(
        "text,expected",
        [("abc", "ABC"), ("Àéîõü", "ÀÉÎÕÜ"), ("a1b2", "A1B2")],
    )
    def test_variants(self, listener, text, expected):
        assert listener.get_transformations(text)["Uppercase"] == expected


class TestLowercase:
    def test_basic(self, listener):
        assert listener.get_transformations("HELLO WORLD")["Lowercase"] == (
            "hello world"
        )

    @pytest.mark.parametrize("text", ["MiXeD", "HELLO", "hello"])
    def test_idempotent(self, listener, text):
        result = listener.get_transformations(text)["Lowercase"]
        assert listener.get_transformations(result)["Lowercase"] == result


class TestTitleCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Title Case"] == "Hello World"

    def test_apostrophe_artifact_is_pinned(self, listener):
        """
        QUIRK: str.title() capitalizes after ANY non-alpha character,
        so apostrophes produce "Don'T". This is standard Python behavior;
        pinned here so replacing str.title() with a smarter title-caser
        shows up as a deliberate, visible change.
        """
        assert listener.get_transformations("don't stop")["Title Case"] == (
            "Don'T Stop"
        )

    def test_digits_boundary_capitalized(self, listener):
        # Same str.title() mechanic: letter after digit gets capitalized
        assert listener.get_transformations("abc 123def")["Title Case"] == (
            "Abc 123Def"
        )


class TestSwapCase:
    def test_basic(self, listener):
        assert listener.get_transformations("Hello World")["Swap Case"] == (
            "hELLO wORLD"
        )

    def test_double_swap_is_identity(self, listener):
        once = listener.get_transformations("MiXeD CaSe")["Swap Case"]
        twice = listener.get_transformations(once)["Swap Case"]

        assert twice == "MiXeD CaSe"

    def test_non_alpha_untouched(self, listener):
        assert listener.get_transformations("a1! b2?")["Swap Case"] == "A1! B2?"


class TestCapitalizeEachWord:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Capitalize Each Word"] == (
            "Hello World"
        )

    def test_rest_of_word_lowered(self, listener):
        # capitalize() lowers the remainder — unlike str.title()
        assert listener.get_transformations("hELLO wORLD")["Capitalize Each Word"] == (
            "Hello World"
        )

    def test_whitespace_collapsed(self, listener):
        assert listener.get_transformations("  a   b  ")["Capitalize Each Word"] == (
            "A B"
        )


class TestCamelCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["CamelCase"] == "HelloWorld"

    def test_three_words(self, listener):
        assert listener.get_transformations("the quick brown")["CamelCase"] == (
            "TheQuickBrown"
        )

    def test_punctuation_retained(self, listener):
        """
        QUIRK: words are split on whitespace only — punctuation stays glued
        to its word inside CamelCase output.
        """
        assert listener.get_transformations("hello world!")["CamelCase"] == (
            "HelloWorld!"
        )

    def test_inner_punctuation_untouched_by_capitalize(self, listener):
        # capitalize() only uppercases char 0 and lowercases the rest;
        # inner apostrophes stay as-is ("It's"), unlike str.title()
        assert listener.get_transformations("it's fine")["CamelCase"] == "It'sFine"


class TestLowerCamelCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Lower CamelCase"] == (
            "helloWorld"
        )

    def test_single_word_fully_lowered(self, listener):
        assert listener.get_transformations("HELLO")["Lower CamelCase"] == "hello"

    def test_first_word_only_first_letter_lowered(self, listener):
        # Only words[0] is .lower()'ed wholesale; the rest keep capitalize()
        assert listener.get_transformations("HELLO WORLD")["Lower CamelCase"] == (
            "helloWorld"
        )

    def test_empty_words_guard(self, listener):
        """
        The conditional expression guards against an empty word list;
        get_transformations('') must not raise IndexError on words[0].
        """
        assert listener.get_transformations("")["Lower CamelCase"] == ""


class TestSnakeCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Snake Case"] == "hello_world"

    def test_all_whitespace_kinds_are_separators(self, listener):
        assert listener.get_transformations("a\tb\nc")["Snake Case"] == "a_b_c"
        assert listener.get_transformations("a  b")["Snake Case"] == "a_b"

    def test_leading_trailing_spaces_dropped(self, listener):
        assert listener.get_transformations("  x  ")["Snake Case"] == "x"


class TestKebabCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Kebab Case"] == "hello-world"

    def test_output_never_contains_spaces(self, listener):
        kebab = listener.get_transformations("some multi word phrase")["Kebab Case"]

        assert " " not in kebab


class TestDotCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Dot Case"] == "hello.world"


class TestSlashCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Slash Case"] == "hello/world"


class TestBackslashCase:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Backslash Case"] == (
            "hello\\world"
        )


class TestReverse:
    def test_basic(self, listener):
        assert listener.get_transformations(CANONICAL)["Reverse"] == "dlrow olleh"

    def test_reversing_twice_is_identity(self, listener):
        once = listener.get_transformations("abcdef")["Reverse"]

        assert listener.get_transformations(once)["Reverse"] == "abcdef"

    def test_unicode_reversal_by_codepoint(self, listener):
        assert listener.get_transformations("café")["Reverse"] == "éfac"


class TestSpongeBobCase:
    def test_alternation_starts_uppercase(self, listener):
        """
        Index 0 is UPPERCASE (i % 2 == 0 -> c.upper()), so the pattern is
        UpPeR-then-lower alternating over the RAW string including spaces.
        """
        assert listener.get_transformations("abc")["SpongeBob Case"] == "AbC"

    def test_spaces_consume_indices(self, listener):
        # Spaces occupy an index even though casing is a no-op on them,
        # shifting the UpPeR phase for every following letter.
        # 'hi there': H(0) i(1) ' '(2) t(3->lower) h(4->upper) e r e ...
        assert listener.get_transformations("hi there")["SpongeBob Case"] == (
            "Hi tHeRe"
        )

    def test_pattern_over_canonical_input(self, listener):
        assert listener.get_transformations(CANONICAL)["SpongeBob Case"] == (
            "HeLlO WoRlD"
        )


# ===========================================================================
# Cross-cutting edge inputs
# ===========================================================================


class TestEmptyAndWhitespaceInputs:
    """Direct calls with degenerate inputs must never raise.

    Two input families behave differently:
      - ''            -> EVERY value is ''
      - whitespace-only -> word-based transforms are '' but string-based
        ones return the (case-flipped) whitespace verbatim
    """

    WORD_BASED: ClassVar[list] = [
        "Capitalize Each Word",
        "CamelCase",
        "Lower CamelCase",
        "Snake Case",
        "Kebab Case",
        "Dot Case",
        "Slash Case",
        "Backslash Case",
    ]

    def test_empty_string_all_values_empty(self, listener):
        result = listener.get_transformations("")

        assert len(result) == len(EXPECTED_ORDER)
        assert all(value == "" for value in result.values())

    @pytest.mark.parametrize("text", [" ", "\t", "\n", "   \n\t  "])
    def test_whitespace_only_never_raises(self, listener, text):
        result = listener.get_transformations(text)

        assert len(result) == len(EXPECTED_ORDER)
        # Word-based transforms have no words to work with
        assert all(result[k] == "" for k in self.WORD_BASED)
        # String-based transforms echo the pure-whitespace input back
        assert result["Uppercase"] == text.upper()
        assert result["Reverse"] == text[::-1]

    def test_whitespace_only_does_not_crash_lower_camel(self, listener):
        # Regression guard for words[0] IndexError potential
        listener.get_transformations("   ")["Lower CamelCase"]


class TestUnicodeInputs:
    """Accents and non-latin scripts flow through every transform."""

    def test_accented_words(self, listener):
        result = listener.get_transformations("café au lait")

        assert result["Uppercase"] == "CAFÉ AU LAIT"
        assert result["Title Case"] == "Café Au Lait"
        assert result["Snake Case"] == "café_au_lait"
        assert result["Reverse"] == "tial ua éfac"
        assert result["CamelCase"] == "CaféAuLait"

    def test_already_uppercase_accents(self, listener):
        assert listener.get_transformations("ÉCOLE")["Lowercase"] == "école"


class TestDigitInputs:
    def test_digits_are_word_content(self, listener):
        result = listener.get_transformations("http 200 ok")

        assert result["Snake Case"] == "http_200_ok"
        assert result["CamelCase"] == "Http200Ok"


class TestStringVsWordBasedWhitespaceHandling:
    """
    Two families coexist: whole-string transforms preserve ALL whitespace,
    word-based transforms collapse it. Both behaviors coexist by design —
    this class documents the distinction explicitly.
    """

    INPUT = "  hello   world  "

    def test_string_based_preserves_everything(self, listener):
        result = listener.get_transformations(self.INPUT)

        # Whitespace positions untouched (only casing flipped / order reversed)
        assert result["Uppercase"] == "  HELLO   WORLD  "
        assert result["Reverse"] == "  dlrow   olleh  "

    def test_word_based_collapses(self, listener):
        result = listener.get_transformations(self.INPUT)

        assert result["Snake Case"] == "hello_world"
        assert result["CamelCase"] == "HelloWorld"


# ===========================================================================
# Structural invariants
# ===========================================================================


class TestStructureInvariants:
    def test_exactly_fourteen_transformations(self, transformations):
        assert len(transformations) == 14

    def test_exact_key_insertion_order(self, transformations):
        """
        Dict insertion order drives the ORDER of Ulauncher result items;
        reordering this list changes what users see first. Pinned exactly.
        """
        assert list(transformations.keys()) == EXPECTED_ORDER

    @pytest.mark.parametrize("text", ["", "one", "two words", "a b c d e"])
    def test_order_stable_across_inputs(self, listener, text):
        assert list(listener.get_transformations(text).keys()) == EXPECTED_ORDER

    def test_names_unique(self, transformations):
        assert len(set(transformations.keys())) == len(EXPECTED_ORDER)

    def test_returns_a_dict(self, listener):
        assert isinstance(listener.get_transformations("anything"), dict)
