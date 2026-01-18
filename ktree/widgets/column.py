"""BrowserColumn widget for displaying lists in columns."""

import logging
from typing import List, Optional
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Input
from textual.binding import Binding
from textual import on
from textual.widgets import OptionList
from ktree.widgets.custom_option_list import HighlightedOptionList

debug_logger = logging.getLogger('debug')


class Selected(Message):
    """Message posted when an item is selected in a column."""

    def __init__(self, column: "BrowserColumn", item: str) -> None:
        """
        Initialize Selected message.

        Args:
            column: The column widget that posted the message.
            item: The selected item value.
        """
        self.column = column
        self.item = item
        super().__init__()


class BrowserColumn(Widget):
    """
    A column widget that displays a list of items with search functionality.

    Structure:
    - Static title at the top
    - SearchInput (hidden by default)
    - HighlightedOptionList for items
    """

    DEFAULT_CSS = """
    BrowserColumn {
        height: 100%;
        border-right: solid $primary;
    }

    BrowserColumn .column-title {
        height: 3;
        text-align: center;
        text-style: bold;
        background: $panel;
        border-bottom: solid $primary;
    }

    BrowserColumn .search-input {
        height: 3;
        border-bottom: solid $primary;
    }

    BrowserColumn .search-input.hidden {
        display: none;
    }

    BrowserColumn .option-list {
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("/", "toggle_search", "Search", show=False),
        Binding("?", "toggle_search", "Search", show=False),
    ]

    def __init__(
        self,
        title: str,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        """
        Initialize BrowserColumn.

        Args:
            title: Title to display at the top of the column.
            id: Optional widget ID.
            classes: Optional CSS classes.
        """
        super().__init__(id=id, classes=classes)
        self.title = title
        self.base_title = title  # Store original title
        self.items: List[str] = []
        self.search_active = False
        self.filtered_items: List[str] = []
        self.is_filtered = False  # Track if filter is currently applied
        self._filter_term: str = ""  # Store the current filter search term
        self._title_widget: Optional[Static] = None
        self.is_loading = False  # Track loading state

    def compose(self):
        """Create child widgets."""
        yield Static(self.title, classes="column-title")
        search_input = Input(
            placeholder="Filter...",
            classes="search-input hidden",
            id=f"{self.id}_search" if self.id else "search",
        )
        yield search_input
        yield HighlightedOptionList(id=f"{self.id}_list" if self.id else "list", classes="option-list")

    def on_mount(self) -> None:
        """Called when widget is mounted."""
        # Get references to child widgets
        self._title_widget = self.query_one(Static)
        self._search_input = self.query_one(Input)
        self._option_list = self.query_one(HighlightedOptionList)
        # Store the calculated width for later use
        self._calculated_width: Optional[int] = None
        # Initialize title (will show asterisk if already filtered)
        self._update_title_with_filter_indicator()

    def set_loading(self, loading: bool = True) -> None:
        """
        Set the loading state of the column.
        
        Args:
            loading: True to show loading state, False to clear it.
        """
        try:
            self.is_loading = loading
            self._option_list.clear_options()
            
            if loading:
                # Show loading message
                self._option_list.add_option("Loading data...")
                self._option_list.disabled = True
                debug_logger.info(f"LOAD: Column '{self.id}' set to loading state")
            else:
                # Re-enable and show actual items
                self._option_list.disabled = False
                # If we have items, they should be set via set_items
                # If no items, set_items will handle showing "No items"
                debug_logger.info(f"LOAD: Column '{self.id}' loading state cleared")
        except Exception as e:
            debug_logger.error(f"LOAD: Error setting loading state in column '{self.id}': {e}", exc_info=True)

    def set_items(self, items: List[str]) -> None:
        """
        Set the items to display in the column.
        If a filter is currently active, it will be re-applied to the new items.

        Args:
            items: List of item names to display.
        """
        self.items = items
        self.is_loading = False  # Clear loading state when items are set
        
        # If there's an active filter, re-apply it to the new items
        if self.is_filtered and self._filter_term:
            debug_logger.info(f"LOAD: Re-applying filter '{self._filter_term}' to {len(items)} new items in column '{self.id}'")
            self.filtered_items = [
                item for item in items if self._filter_term in item.lower()
            ]
            debug_logger.info(f"LOAD: Filtered to {len(self.filtered_items)} items")
        else:
            # No active filter, show all items
            self.filtered_items = items
        
        self._option_list.clear_options()
        self._option_list.disabled = False  # Re-enable the list
        
        # Handle empty state
        if len(self.filtered_items) == 0:
            # Show "No items" message
            self._option_list.add_option("No items")
            self._option_list.disabled = True
            debug_logger.info(f"LOAD: Column '{self.id}' has no items, showing 'No items' message")
        else:
            # Add filtered items (or all items if no filter)
            for item in self.filtered_items:
                self._option_list.add_option(item)
        
        # Calculate width based on max content length (use all items, not filtered, for consistent width)
        if len(items) > 0:
            # Find the longest item name from all items (not just filtered)
            max_item_length = max(len(item) for item in items)
            # Also consider the title length
            title_length = len(self.title)
            # Use the maximum of item length, title length, or minimum width
            max_length = max(max_item_length, title_length, 15)
            # Add padding for borders, spacing, and OptionList internal padding
            # Left border (1) + right border (1) + OptionList padding (2-4) + safety margin (2)
            column_width = max_length + 8
            self._calculated_width = column_width
            # Set the width immediately and also with a timer to ensure it sticks
            self.styles.width = column_width
            debug_logger.info(f"LOAD: Setting column '{self.id}' width to {column_width} (max_length={max_length}, items={len(items)}, filtered={len(self.filtered_items)})")
            # Also set with a timer in case layout hasn't happened yet
            def set_width():
                if self._calculated_width:
                    self.styles.width = self._calculated_width
                    debug_logger.info(f"LOAD: Re-set column '{self.id}' width to {self._calculated_width}")
            self.set_timer(0.05, set_width)
            self.set_timer(0.2, set_width)  # Try again after layout
            
            # Explicitly set the highlighted index to 0 (first filtered item)
            # Only do this if we have items and the list is enabled
            if len(self.filtered_items) > 0 and not self._option_list.disabled:
                try:
                    # Set highlighted index
                    self._option_list.highlighted = 0
                    
                    # Post selection message for first filtered item (for cascading selection)
                    # Use call_later to ensure widget is ready
                    # Double-check that filtered_items still has items when the callback executes
                    def post_selection():
                        try:
                            if (len(self.filtered_items) > 0 and 
                                not self._option_list.disabled and
                                self._option_list.highlighted is not None):
                                self.post_message(Selected(self, self.filtered_items[0]))
                        except Exception as e:
                            debug_logger.warning(f"LOAD: Error in post_selection callback for column '{self.id}': {e}")
                    self.call_later(post_selection)
                except Exception as e:
                    debug_logger.warning(f"LOAD: Error setting highlight in column '{self.id}': {e}")
        else:
            # Default width for empty columns (based on title)
            title_length = len(self.title)
            column_width = max(15, title_length + 8)
            self.styles.width = column_width
            debug_logger.info(f"LOAD: Setting empty column '{self.id}' width to {column_width} (title_length={title_length})")
            # Also set with a timer
            def set_width():
                self.styles.width = column_width
            self.set_timer(0.05, set_width)

    def action_toggle_search(self) -> None:
        """Toggle search input visibility."""
        debug_logger.info(f"ACTION: toggle_search in column '{self.id}' (currently active: {self.search_active})")
        if self.search_active:
            # Hide search and clear filter
            self._search_input.add_class("hidden")
            self.search_active = False
            self._search_input.value = ""
            self.filtered_items = self.items
            self.is_filtered = False
            self._update_title_with_filter_indicator()
            self._update_list()
            self._option_list.focus()
        else:
            # Show search input
            self._search_input.remove_class("hidden")
            self.search_active = True
            self._search_input.focus()
    
    def _update_title_with_filter_indicator(self) -> None:
        """Update the column title to show/hide the red asterisk when filtered."""
        if not self._title_widget:
            return
        if self.is_filtered:
            # Add red asterisk to title using Textual markup
            # Textual supports [red]...[/red] markup syntax
            self._title_widget.update(f"[red]{self.base_title}*[/red]")
            debug_logger.info(f"ACTION: Added filter indicator (*) to column '{self.id}' title")
        else:
            # Show normal title
            self._title_widget.update(self.base_title)
            debug_logger.info(f"ACTION: Removed filter indicator from column '{self.id}' title")

    def _update_list(self) -> None:
        """Update the option list with filtered items."""
        self._option_list.clear_options()
        
        if len(self.filtered_items) == 0:
            # Show "No items" message
            self._option_list.add_option("No items")
            self._option_list.disabled = True
            debug_logger.info(f"LOAD: Column '{self.id}' has no filtered items, showing 'No items' message")
        else:
            # Re-enable and show filtered items
            self._option_list.disabled = False
            for item in self.filtered_items:
                self._option_list.add_option(item)
            self._option_list.highlighted = 0
            # Recalculate width based on filtered items
            max_item_length = max(len(item) for item in self.filtered_items) if self.filtered_items else 0
            title_length = len(self.title)
            max_length = max(max_item_length, title_length, 15)
            column_width = max_length + 8
            self.styles.width = column_width
            debug_logger.info(f"LOAD: Updated column '{self.id}' width to {column_width} after filtering (max_length={max_length})")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes - don't filter yet, just show the input."""
        # Don't filter in real-time - wait for Enter key
        # This allows user to type the full filter before applying
        pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission (Enter key) - apply filter."""
        if event.input == self._search_input:
            search_term = event.value.lower()
            self._filter_term = search_term  # Store the filter term
            debug_logger.info(f"ACTION: Applying filter in column '{self.id}' with term: '{search_term}'")
            
            if search_term:
                # Apply filter
                self.filtered_items = [
                    item for item in self.items if search_term in item.lower()
                ]
                self.is_filtered = True
                # Update title with red asterisk
                self._update_title_with_filter_indicator()
            else:
                # Empty search - show all items
                self.filtered_items = self.items
                self.is_filtered = False
                self._filter_term = ""  # Clear filter term
                self._update_title_with_filter_indicator()
            
            self._update_list()
            # Keep search input visible, just return focus to list
            self._option_list.focus()

    def on_key(self, event) -> None:
        """Handle key events, specifically ESC to cancel search."""
        if self.search_active and event.key == "escape":
            debug_logger.info(f"ACTION: ESC pressed in column '{self.id}' - canceling filter")
            # Cancel search and restore full list
            self._search_input.add_class("hidden")
            self.search_active = False
            self._search_input.value = ""
            self.filtered_items = self.items
            self.is_filtered = False
            self._filter_term = ""  # Clear filter term
            self._update_title_with_filter_indicator()
            self._update_list()
            self._option_list.focus()
            event.stop()
        # For other keys, let them be handled by the default widget behavior
        # (no need to call super() as Widget doesn't have on_key)

    def on_option_list_option_selected(self, event: HighlightedOptionList.OptionSelected) -> None:
        """Handle option selection."""
        selected_item = event.option.prompt
        # Don't post selection for placeholder messages
        if selected_item in ("Loading data...", "No items"):
            debug_logger.info(f"ACTION: Ignoring selection of placeholder message: {selected_item}")
            return
        self.post_message(Selected(self, selected_item))

    @on(OptionList.OptionHighlighted)
    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Handle option highlighting (when navigating with arrows)."""
        # Don't post selection messages if the list is disabled (loading or empty)
        if self._option_list.disabled:
            debug_logger.info(f"ACTION: OptionHighlighted event ignored - column '{self.id}' is disabled")
            return
        
        # Post selection message on highlight for cascading selection
        # This ensures objects load when navigating with arrow keys
        debug_logger.info(f"ACTION: OptionHighlighted event in column {self.id}")
        try:
            selected_item = event.option.prompt
            # Don't post selection for placeholder messages
            if selected_item in ("Loading data...", "No items"):
                debug_logger.info(f"ACTION: Ignoring selection of placeholder message: {selected_item}")
                return
            debug_logger.info(f"ACTION: Posting Selected message for item: {selected_item}")
            self.post_message(Selected(self, selected_item))
        except (AttributeError, IndexError) as e:
            debug_logger.warning(f"ACTION: Error getting item from event: {e}")
            # Fallback: get item from highlighted index
            if self._option_list.highlighted is not None:
                idx = self._option_list.highlighted
                if idx < len(self.filtered_items):
                    selected_item = self.filtered_items[idx]
                    debug_logger.info(f"ACTION: Posting Selected message (fallback) for item: {selected_item}")
                    self.post_message(Selected(self, selected_item))
                else:
                    debug_logger.warning(f"ACTION: Index {idx} out of range for filtered_items (len={len(self.filtered_items)})")
            else:
                debug_logger.warning("ACTION: highlighted is None, cannot post Selected message")

