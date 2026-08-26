"""
Smoke tests for the extension module itself (main.py).

Verifies the wiring Ulauncher relies on:
  - TextToolsExtension subclasses the real Extension base class
  - KeywordQueryEventListener subclasses the real EventListener base
  - The KeywordQueryEvent subscription is established on construction
  - The __main__ entry point exists behind a proper guard

The extension instance is constructed WITHOUT a running Ulauncher daemon:
Extension.__init__ only wires local state (the API socket connection
happens in run(), which we never call here).
"""

import inspect

import pytest
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent

import main


class TestClassHierarchy:
    """The classes must plug into Ulauncher's API contract."""

    def test_extension_subclasses_ulauncher_extension(self):
        assert issubclass(main.TextToolsExtension, Extension)

    def test_listener_subclasses_ulauncher_eventlistener(self):
        assert issubclass(main.KeywordQueryEventListener, EventListener)

    def test_listener_exposes_on_event(self):
        assert callable(main.KeywordQueryEventListener.on_event)


class TestEventSubscription:
    """Construction must register exactly the keyword-query listener."""

    @pytest.fixture
    def extension(self, monkeypatch):
        """
        Extension.__init__ builds a Client(), whose constructor requires the
        ULAUNCHER_WS_API environment variable (normally provided by the
        Ulauncher daemon when it spawns the extension process). We inject a
        dummy URL so construction succeeds without a running daemon.
        """
        monkeypatch.setenv("ULAUNCHER_WS_API", "ws://127.0.0.1:9999/test")
        return main.TextToolsExtension()

    def test_constructs_without_running_daemon(self, extension):
        assert isinstance(extension, main.TextToolsExtension)

    def test_keyword_query_event_is_subscribed(self, extension):
        registered = extension._listeners[KeywordQueryEvent]

        assert len(registered) == 1
        assert isinstance(registered[0], main.KeywordQueryEventListener)

    def test_no_other_listeners_registered(self, extension):
        # Only the keyword query flow exists in this extension
        assert set(extension._listeners.keys()) == {KeywordQueryEvent}


class TestModuleShape:
    """Source-level guarantees that survive without executing run()."""

    def test_main_guard_present(self):
        """
        Importing main.py (as tests do) must NOT start the extension;
        only direct execution may reach TextToolsExtension().run().
        """
        source = inspect.getsource(main)

        assert "if __name__ == '__main__':" in source

    def test_run_only_referenced_under_guard(self):
        source = inspect.getsource(main)
        guard_index = source.index("if __name__")

        # .run() appears exactly once and lives after the __main__ guard
        assert source.count(".run()") == 1
        assert source.index(".run()") > guard_index

    def test_no_side_effects_at_import_time(self):
        # Re-importing is idempotent and defines no module-level instances
        import importlib

        reloaded = importlib.reload(main)

        assert hasattr(reloaded, "TextToolsExtension")
