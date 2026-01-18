"""DetailsPanel widget for displaying object details with scrolling and filtering."""

import logging
from typing import Optional
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.containers import ScrollableContainer
from textual.binding import Binding
from textual import on

debug_logger = logging.getLogger('debug')


class DetailsPanel(Widget, can_focus=True):
    """
    A scrollable, focusable panel for displaying object details with filtering.
    
    Structure:
    - SearchInput (hidden by default)
    - ScrollableContainer with Static content
    """

    DEFAULT_CSS = """
    DetailsPanel {
        height: 100%;
        border-left: solid $primary;
        background: $surface;
    }
    
    DetailsPanel:focus {
        border-left: solid $primary;
        background: $panel;
    }

    DetailsPanel .details-title {
        height: 3;
        text-align: center;
        text-style: bold;
        background: $panel;
        border-bottom: solid $primary;
    }

    DetailsPanel .search-input {
        height: 3;
        border-bottom: solid $primary;
    }

    DetailsPanel .search-input.hidden {
        display: none;
    }

    DetailsPanel #details-scrollable {
        height: 1fr;
        scrollbar-size-horizontal: 0;
        scrollbar-size-vertical: 1;
    }

    DetailsPanel #details-text {
        padding: 1;
        width: 100%;
        height: auto;
        scrollbar-size: 0 0;
        overflow: hidden;
    }
    
    DetailsPanel ScrollableContainer Static {
        scrollbar-size: 0 0;
        overflow: hidden;
        height: auto;
        width: 100%;
    }
    """

    BINDINGS = [
        Binding("/", "toggle_search", "Search", show=False),
        Binding("?", "toggle_search", "Search", show=False),
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
    ]

    def __init__(
        self,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """
        Initialize DetailsPanel.

        Args:
            id: Optional widget ID.
            classes: Optional CSS classes.
        """
        super().__init__(id=id, classes=classes)
        self.search_active = False
        self._original_content: str = ""
        self._filtered_content: str = ""
        self._filter_term: str = ""
        self._title_widget: Optional[Static] = None
        self._search_input: Optional[Input] = None
        self._content_widget: Optional[Static] = None

    def compose(self):
        """Create child widgets."""
        yield Static("Describe", classes="details-title")
        search_input = Input(
            placeholder="Filter content...",
            classes="search-input hidden",
            id="details_search",
        )
        yield search_input
        with ScrollableContainer(id="details-scrollable"):
            yield Static("Select an object to view details...", id="details-text")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Get references to child widgets
        self._title_widget = self.query_one(".details-title", Static)
        self._search_input = self.query_one(Input)
        self._content_widget = self.query_one("#details-text", Static)

    def update_title(self, is_pod: bool = False) -> None:
        """
        Update the title based on whether the selected object is a Pod.
        
        Args:
            is_pod: True if the selected object is a Pod, False otherwise.
        """
        if self._title_widget:
            if is_pod:
                self._title_widget.update("Describe (d) Logs (g) Exec (e)")
            else:
                self._title_widget.update("Describe")
            debug_logger.info(f"ACTION: Updated details panel title (is_pod={is_pod})")

    def scroll_to_bottom(self) -> None:
        """Scroll the details panel content to the bottom."""
        scrollable = self.query_one("#details-scrollable", ScrollableContainer)
        if scrollable:
            try:
                # Try scroll_end method first (if available in Textual)
                if hasattr(scrollable, 'scroll_end'):
                    scrollable.scroll_end(animate=False)
                    debug_logger.info(f"ACTION: Called scroll_end() on ScrollableContainer")
                # Try scroll_to with a very large y value to reach the bottom
                elif hasattr(scrollable, 'scroll_to'):
                    # Use a very large number to ensure we scroll to the bottom
                    scrollable.scroll_to(y=999999, animate=False)
                    debug_logger.info(f"ACTION: Called scroll_to(y=999999) on ScrollableContainer")
                # Alternative: try to get the virtual size and scroll to it
                elif hasattr(scrollable, 'virtual_size'):
                    try:
                        virtual_height = scrollable.virtual_size.height
                        if virtual_height > 0:
                            scrollable.scroll_to(y=virtual_height, animate=False)
                            debug_logger.info(f"ACTION: Scrolled to bottom using virtual_size.height={virtual_height}")
                    except Exception as e:
                        debug_logger.warning(f"ACTION: Error using virtual_size: {e}")
                else:
                    debug_logger.warning(f"ACTION: ScrollableContainer has no scroll methods for scrolling to bottom")
            except Exception as e:
                debug_logger.error(f"ACTION: Error scrolling to bottom: {e}", exc_info=True)

    def update_content(self, content: str, scroll_to_bottom: bool = False) -> None:
        """
        Update the content displayed in the details panel.

        Args:
            content: The content to display.
            scroll_to_bottom: If True, scroll to the bottom after updating content.
        """
        self._original_content = content
        self._filtered_content = content
        
        # If there's an active filter, re-apply it
        if self.search_active and self._filter_term:
            self._apply_filter(self._filter_term)
        else:
            if self._content_widget:
                self._content_widget.update(content)
            debug_logger.info(f"LOAD: Updated details panel content ({len(content)} chars)")
        
        # Scroll to bottom if requested (e.g., for logs)
        if scroll_to_bottom:
            # Use call_after_refresh to ensure content is rendered and layout is updated
            self.call_after_refresh(self.scroll_to_bottom)

    def _apply_filter(self, search_term: str) -> None:
        """
        Apply filter to the content, highlighting matching lines.

        Args:
            search_term: The search term to filter by.
        """
        if not self._original_content:
            return
        
        self._filter_term = search_term.lower()
        lines = self._original_content.split('\n')
        
        if search_term:
            # Filter lines that contain the search term
            filtered_lines = [
                line for line in lines
                if search_term.lower() in line.lower()
            ]
            self._filtered_content = '\n'.join(filtered_lines)
            debug_logger.info(f"ACTION: Filtered details content with term '{search_term}' ({len(filtered_lines)}/{len(lines)} lines)")
        else:
            # Show all content
            self._filtered_content = self._original_content
            debug_logger.info(f"ACTION: Cleared details filter")
        
        if self._content_widget:
            self._content_widget.update(self._filtered_content)

    def action_toggle_search(self) -> None:
        """Toggle search input visibility."""
        if not self._search_input:
            return
        
        self.search_active = not self.search_active
        debug_logger.info(f"ACTION: toggle_search in details panel (currently active: {self.search_active})")
        
        if self.search_active:
            self._search_input.remove_class("hidden")
            self._search_input.focus()
        else:
            self._search_input.add_class("hidden")
            self._search_input.value = ""
            self._filter_term = ""
            # Restore original content
            if self._content_widget:
                self._content_widget.update(self._original_content)
            # Focus back to the scrollable container
            scrollable = self.query_one("#details-scrollable", ScrollableContainer)
            if scrollable:
                scrollable.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission (Enter key) - apply filter."""
        if event.input == self._search_input:
            search_term = event.value
            self._apply_filter(search_term)
            # Keep search input visible, just return focus to scrollable
            scrollable = self.query_one("#details-scrollable", ScrollableContainer)
            if scrollable:
                scrollable.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes - apply filter in real-time."""
        if event.input == self._search_input:
            search_term = event.value
            self._apply_filter(search_term)

    def action_scroll_up(self) -> None:
        """Scroll the details panel content up."""
        debug_logger.info(f"ACTION: action_scroll_up called in DetailsPanel")
        scrollable = self.query_one("#details-scrollable", ScrollableContainer)
        if scrollable:
            try:
                # Try scroll_up method first
                if hasattr(scrollable, 'scroll_up'):
                    scrollable.scroll_up()
                    debug_logger.info(f"ACTION: Called scroll_up() on ScrollableContainer")
                # Try scroll method
                elif hasattr(scrollable, 'scroll'):
                    scrollable.scroll(0, -1, animate=False)
                    debug_logger.info(f"ACTION: Called scroll(0, -1) on ScrollableContainer")
                # Try scroll_to with current offset
                elif hasattr(scrollable, 'scroll_to'):
                    try:
                        # Get current scroll offset
                        scroll_offset = scrollable.scroll_offset
                        if hasattr(scroll_offset, 'y'):
                            new_y = max(0, scroll_offset.y - 1)
                            scrollable.scroll_to(y=new_y, animate=False)
                            debug_logger.info(f"ACTION: Called scroll_to(y={new_y}) on ScrollableContainer")
                        else:
                            debug_logger.warning(f"ACTION: scroll_offset.y not available, offset={scroll_offset}")
                    except AttributeError:
                        debug_logger.warning(f"ACTION: scroll_offset not available on ScrollableContainer")
                else:
                    debug_logger.warning(f"ACTION: ScrollableContainer has no scroll methods. Available methods: {[m for m in dir(scrollable) if 'scroll' in m.lower()]}")
            except Exception as e:
                debug_logger.error(f"ACTION: Error scrolling details panel up: {e}", exc_info=True)

    def action_scroll_down(self) -> None:
        """Scroll the details panel content down."""
        debug_logger.info(f"ACTION: action_scroll_down called in DetailsPanel")
        scrollable = self.query_one("#details-scrollable", ScrollableContainer)
        if scrollable:
            try:
                # Try scroll_down method first
                if hasattr(scrollable, 'scroll_down'):
                    scrollable.scroll_down()
                    debug_logger.info(f"ACTION: Called scroll_down() on ScrollableContainer")
                # Try scroll method
                elif hasattr(scrollable, 'scroll'):
                    scrollable.scroll(0, 1, animate=False)
                    debug_logger.info(f"ACTION: Called scroll(0, 1) on ScrollableContainer")
                # Try scroll_to with current offset
                elif hasattr(scrollable, 'scroll_to'):
                    try:
                        # Get current scroll offset
                        scroll_offset = scrollable.scroll_offset
                        if hasattr(scroll_offset, 'y'):
                            new_y = scroll_offset.y + 1
                            scrollable.scroll_to(y=new_y, animate=False)
                            debug_logger.info(f"ACTION: Called scroll_to(y={new_y}) on ScrollableContainer")
                        else:
                            debug_logger.warning(f"ACTION: scroll_offset.y not available, offset={scroll_offset}")
                    except AttributeError:
                        debug_logger.warning(f"ACTION: scroll_offset not available on ScrollableContainer")
                else:
                    debug_logger.warning(f"ACTION: ScrollableContainer has no scroll methods. Available methods: {[m for m in dir(scrollable) if 'scroll' in m.lower()]}")
            except Exception as e:
                debug_logger.error(f"ACTION: Error scrolling details panel down: {e}", exc_info=True)

    def on_key(self, event) -> None:
        """Handle key events, specifically ESC to cancel search."""
        if self.search_active and event.key == "escape":
            debug_logger.info(f"ACTION: ESC pressed in details panel - canceling filter")
            # Cancel search and restore full content
            if self._search_input:
                self._search_input.add_class("hidden")
                self._search_input.value = ""
            self.search_active = False
            self._filter_term = ""
            if self._content_widget:
                self._content_widget.update(self._original_content)
            # Focus back to the scrollable container
            scrollable = self.query_one("#details-scrollable", ScrollableContainer)
            if scrollable:
                scrollable.focus()
            event.stop()

