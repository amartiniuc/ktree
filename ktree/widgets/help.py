"""HelpOverlay widget for displaying keybindings help."""

import logging
from typing import Optional
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Container

debug_logger = logging.getLogger('debug')


class HelpOverlay(Widget):
    """
    A help overlay widget that displays keybindings.
    
    Features:
    - Appears at bottom of screen (60% width, centered)
    - Toggled with CTRL+B
    - Non-interactive (doesn't block main app)
    """

    DEFAULT_CSS = """
    HelpOverlay {
        width: 60%;
        height: auto;
        dock: bottom;
        offset-y: 1;
        offset-x: 20%;
        background: $panel;
        border: solid $primary;
        padding: 1;
        layer: overlay;
        display: none;
    }
    
    HelpOverlay.visible {
        display: block;
    }
    
    HelpOverlay .help-title {
        text-align: center;
        text-style: bold;
        padding: 1;
        border-bottom: solid $primary;
        margin-bottom: 1;
    }
    
    HelpOverlay .help-content {
        padding: 1;
    }
    
    HelpOverlay .help-section {
        margin-bottom: 1;
    }
    
    HelpOverlay .help-section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    HelpOverlay .help-binding {
        margin-left: 2;
        margin-bottom: 1;
    }
    
    HelpOverlay .help-key {
        color: $warning;
        text-style: bold;
    }
    
    HelpOverlay .help-intro {
        margin-bottom: 2;
        padding: 1;
        border-bottom: solid $primary;
    }
    
    HelpOverlay .help-intro-text {
        text-align: center;
        margin-bottom: 1;
    }
    """

    def __init__(
        self,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """
        Initialize HelpOverlay.

        Args:
            id: Optional widget ID.
            classes: Optional CSS classes.
        """
        super().__init__(id=id, classes=classes)
        self._visible = False

    def compose(self):
        """Create child widgets."""
        with Container():
            yield Static("Keybindings", classes="help-title")
            with Container(classes="help-content"):
                # Introduction
                with Container(classes="help-intro"):
                    yield Static("KTree - Kubernetes Browser", classes="help-intro-text")
                    yield Static(
                        "Browse your Kubernetes cluster using a tree-based interface. "
                        "Navigate through namespaces → object types → objects → details. "
                        "Use vim-style keys (h/j/k/l) or arrow keys to move around.",
                        classes="help-binding"
                    )
                
                # Navigation
                with Container(classes="help-section"):
                    yield Static("Navigation", classes="help-section-title")
                    yield Static("q - Quit the application", classes="help-binding")
                    yield Static("h / ← - Move focus left (between panels)", classes="help-binding")
                    yield Static("j / ↓ - Move down (within list)", classes="help-binding")
                    yield Static("k / ↑ - Move up (within list)", classes="help-binding")
                    yield Static("l / → - Move focus right (between panels)", classes="help-binding")
                
                # Search/Filter
                with Container(classes="help-section"):
                    yield Static("Search & Filter", classes="help-section-title")
                    yield Static("/ or ? - Toggle search/filter in current column", classes="help-binding")
                    yield Static("Enter - Apply filter", classes="help-binding")
                    yield Static("ESC - Clear filter", classes="help-binding")
                
                # Actions
                with Container(classes="help-section"):
                    yield Static("Actions", classes="help-section-title")
                    yield Static("r - Refresh current data", classes="help-binding")
                    yield Static("d - Describe view (show YAML details)", classes="help-binding")
                    yield Static("g - View logs (for Pods, auto-scrolls to bottom)", classes="help-binding")
                    yield Static("e - Show exec commands (for Pods)", classes="help-binding")
                    yield Static("CTRL+1-4 - Copy exec commands to clipboard", classes="help-binding")
                
                # Help
                with Container(classes="help-section"):
                    yield Static("Help", classes="help-section-title")
                    yield Static("CTRL+B - Toggle this help overlay", classes="help-binding")

    def toggle(self) -> None:
        """Toggle the visibility of the help overlay."""
        self._visible = not self._visible
        debug_logger.info(f"ACTION: Toggling help overlay (visible={self._visible})")
        
        if self._visible:
            self.add_class("visible")
        else:
            self.remove_class("visible")

    def is_visible(self) -> bool:
        """Check if the help overlay is currently visible."""
        return self._visible

