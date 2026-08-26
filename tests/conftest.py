"""
Pytest configuration for the Text Tools extension test suite.

Adds the project root to sys.path so `import main` resolves exactly like
it does when Ulauncher launches the extension (extension root on sys.path).
"""

import os
import sys

import pytest

# ---------------------------------------------------------------------------
# Path setup: mirror Ulauncher's runtime layout. The extension is launched
# with its own directory as the working root, so plain `import main` works.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


@pytest.fixture
def listener():
    """A fresh KeywordQueryEventListener instance (stateless, but cheap)."""
    from main import KeywordQueryEventListener

    return KeywordQueryEventListener()


@pytest.fixture
def transformations(listener):
    """
    The full transformation dict for a canonical two-word input.

    Handy for structural assertions that should not depend on one
    particular transformation behaving correctly.
    """
    return listener.get_transformations("hello world")
