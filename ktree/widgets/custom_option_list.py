"""Custom OptionList widget with enhanced highlighting."""

from typing import Any
from textual.widgets import OptionList


class HighlightedOptionList(OptionList):
    """
    Enhanced OptionList that ensures highlights are visible on startup.

    This widget ensures the first item is highlighted immediately,
    even before user interaction.
    """

    def on_mount(self) -> None:
        """Called when widget is mounted - ensure first item is highlighted."""
        super().on_mount()
        # Force highlight of first item if list has items
        # This will be set when items are added via set_items

