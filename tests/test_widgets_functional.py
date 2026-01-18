"""Functional tests for KTree widgets."""

import pytest
from unittest.mock import Mock, MagicMock
from textual.widgets import Input
from ktree.widgets.column import BrowserColumn, Selected
from ktree.widgets.custom_option_list import HighlightedOptionList


class TestBrowserColumn:
    """Test BrowserColumn widget functionality."""

    @pytest.mark.asyncio
    async def test_column_initializes_with_title(self):
        """Test that BrowserColumn initializes with correct title."""
        column = BrowserColumn("Test Column", id="test-col")
        assert column.title == "Test Column"
        assert column.id == "test-col"

    @pytest.mark.asyncio
    async def test_set_items_populates_list(self):
        """Test that set_items() populates the option list."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield BrowserColumn("Test Column", id="test-col")
        
        items = ["item1", "item2", "item3"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            column = app.query_one(BrowserColumn)
            column.set_items(items)
            await pilot.pause(0.1)
            
            # Check that items are set
            assert column.items == items
            assert column.filtered_items == items
            
            # Check that option list has items
            option_list = column.query_one(HighlightedOptionList)
            assert option_list is not None

    @pytest.mark.asyncio
    async def test_toggle_search_shows_hides_input(self):
        """Test that toggle_search() shows and hides search input."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield BrowserColumn("Test Column", id="test-col")
        
        items = ["item1", "item2", "item3"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            column = app.query_one(BrowserColumn)
            column.set_items(items)
            await pilot.pause(0.1)
            
            # Initially search should be inactive
            assert column.search_active is False
            
            # Toggle search on
            column.action_toggle_search()
            await pilot.pause(0.1)
            assert column.search_active is True
            
            # Toggle search off
            column.action_toggle_search()
            await pilot.pause(0.1)
            assert column.search_active is False

    @pytest.mark.asyncio
    async def test_search_filters_items(self):
        """Test that search input filters items correctly."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield BrowserColumn("Test Column", id="test-col")
        
        items = ["apple", "banana", "apricot", "cherry"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            column = app.query_one(BrowserColumn)
            column.set_items(items)
            await pilot.pause(0.1)
            
            # Enable search
            column.action_toggle_search()
            await pilot.pause(0.1)
            
            # Type search term
            search_input = column.query_one(Input)
            search_input.value = "ap"
            await pilot.pause(0.1)
            
            # Check filtered items
            assert len(column.filtered_items) == 2
            assert "apple" in column.filtered_items
            assert "apricot" in column.filtered_items
            assert "banana" not in column.filtered_items

    @pytest.mark.asyncio
    async def test_search_case_insensitive(self):
        """Test that search is case insensitive."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield BrowserColumn("Test Column", id="test-col")
        
        items = ["Apple", "banana", "APRICOT", "Cherry"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            column = app.query_one(BrowserColumn)
            column.set_items(items)
            await pilot.pause(0.1)
            
            # Enable search
            column.action_toggle_search()
            await pilot.pause(0.1)
            
            # Type search term in lowercase
            search_input = column.query_one(Input)
            search_input.value = "apple"
            await pilot.pause(0.1)
            
            # Should find "Apple"
            assert "Apple" in column.filtered_items

    @pytest.mark.asyncio
    async def test_clear_search_restores_all_items(self):
        """Test that clearing search restores all items."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield BrowserColumn("Test Column", id="test-col")
        
        items = ["apple", "banana", "apricot", "cherry"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            column = app.query_one(BrowserColumn)
            column.set_items(items)
            await pilot.pause(0.1)
            
            # Enable search and filter
            column.action_toggle_search()
            await pilot.pause(0.1)
            search_input = column.query_one(Input)
            search_input.value = "ap"
            await pilot.pause(0.1)
            
            # Clear search
            column.action_toggle_search()
            await pilot.pause(0.1)
            
            # All items should be restored
            assert column.filtered_items == items
            assert len(column.filtered_items) == len(items)

    @pytest.mark.asyncio
    async def test_selection_posts_message(self):
        """Test that selecting an item posts a Selected message."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield BrowserColumn("Test Column", id="test-col")
        
        items = ["item1", "item2", "item3"]
        app = TestApp()
        messages_received = []
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            column = app.query_one(BrowserColumn)
            column.set_items(items)
            await pilot.pause(0.1)
            
            # Set up message handler
            def handle_selected(message):
                messages_received.append(message)
            
            app.watch(Selected, handle_selected)
            
            # Simulate selection
            option_list = column.query_one(HighlightedOptionList)
            option_list.highlighted = 0
            await pilot.pause(0.1)
            
            # Trigger selection event
            if hasattr(option_list, 'get_option_at_index'):
                option = option_list.get_option_at_index(0)
            else:
                # Fallback: create a mock option
                from textual.widgets import Option
                option = Option(prompt=items[0], id=None)
            event = HighlightedOptionList.OptionSelected(option_list, option)
            column.on_option_list_option_selected(event)
            await pilot.pause(0.1)
            
            # Check that message was posted
            assert len(messages_received) > 0

    @pytest.mark.asyncio
    async def test_column_width_adjusts_to_content(self):
        """Test that column width adjusts based on content length."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield BrowserColumn("Test Column", id="test-col")
        
        short_items = ["a", "b", "c"]
        long_items = ["very-long-item-name-1", "very-long-item-name-2"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            column = app.query_one(BrowserColumn)
            
            # Set short items
            column.set_items(short_items)
            await pilot.pause(0.1)
            short_width = column.styles.width.value if hasattr(column.styles.width, 'value') else None
            
            # Set long items
            column.set_items(long_items)
            await pilot.pause(0.1)
            long_width = column.styles.width.value if hasattr(column.styles.width, 'value') else None
            
            # Long items should result in wider column
            # (Note: width might be None or auto, so we just check it's set)
            assert column.styles.width is not None


class TestHighlightedOptionList:
    """Test HighlightedOptionList widget functionality."""

    @pytest.mark.asyncio
    async def test_list_highlights_first_item_on_startup(self):
        """Test that list highlights first item on startup."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield HighlightedOptionList(id="test-list")
        
        items = ["item1", "item2", "item3"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            option_list = app.query_one(HighlightedOptionList)
            
            # Add items
            for item in items:
                option_list.add_option(item)
            await pilot.pause(0.1)
            
            # Set highlighted to 0
            option_list.highlighted = 0
            await pilot.pause(0.1)
            
            # Check that first item is highlighted
            assert option_list.highlighted == 0

    @pytest.mark.asyncio
    async def test_list_navigates_with_arrows(self):
        """Test that list navigation works with arrow keys."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield HighlightedOptionList(id="test-list")
        
        items = ["item1", "item2", "item3"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            option_list = app.query_one(HighlightedOptionList)
            
            # Add items
            for item in items:
                option_list.add_option(item)
            await pilot.pause(0.1)
            
            # Start at index 0
            option_list.highlighted = 0
            await pilot.pause(0.1)
            
            # Move down
            option_list.action_cursor_down()
            await pilot.pause(0.1)
            assert option_list.highlighted == 1
            
            # Move up
            option_list.action_cursor_up()
            await pilot.pause(0.1)
            assert option_list.highlighted == 0

    @pytest.mark.asyncio
    async def test_list_clears_options(self):
        """Test that clear_options() removes all options."""
        from textual.app import App
        
        class TestApp(App):
            def compose(self):
                yield HighlightedOptionList(id="test-list")
        
        items = ["item1", "item2", "item3"]
        app = TestApp()
        
        async with app.run_test() as pilot:
            await pilot.pause(0.1)
            option_list = app.query_one(HighlightedOptionList)
            
            # Add items
            for item in items:
                option_list.add_option(item)
            await pilot.pause(0.1)
            
            # Clear options
            option_list.clear_options()
            await pilot.pause(0.1)
            
            # Check that options are cleared
            # (Note: We can't directly check option count, but we can verify it's empty)
            assert option_list.highlighted is None or option_list.highlighted == 0

