"""Functional tests for KTreeApp."""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from textual.app import App
from textual.widgets import Static
from ktree.app import KTreeApp
from ktree.widgets.column import BrowserColumn, Selected
from ktree.widgets.custom_option_list import HighlightedOptionList


class TestAppInitialization:
    """Test application initialization and startup."""

    @pytest.mark.asyncio
    async def test_app_initializes_with_defaults(self, mock_k8s_manager):
        """Test that app initializes with default parameters."""
        app = KTreeApp()
        assert app.initial_context is None
        assert app.initial_namespace is None
        assert app.initial_type is None
        assert app.k8s is None
        assert app.current_col_idx == 0

    @pytest.mark.asyncio
    async def test_app_initializes_with_context(self, mock_k8s_manager):
        """Test that app initializes with specified context."""
        app = KTreeApp(initial_context="test-context")
        assert app.initial_context == "test-context"

    @pytest.mark.asyncio
    async def test_app_initializes_with_namespace(self, mock_k8s_manager):
        """Test that app initializes with specified namespace."""
        app = KTreeApp(initial_namespace="default")
        assert app.initial_namespace == "default"

    @pytest.mark.asyncio
    async def test_app_initializes_with_type(self, mock_k8s_manager):
        """Test that app initializes with specified object type."""
        app = KTreeApp(initial_type="Pods")
        assert app.initial_type == "Pods"

    @pytest.mark.asyncio
    async def test_app_compose_creates_widgets(self, mock_k8s_manager):
        """Test that compose() creates all required widgets."""
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.1)
                # Check that columns are created
                assert app.col_ns is not None
                assert app.col_types is not None
                assert app.col_objects is not None
                assert len(app.columns) == 3
                
                # Check that columns have correct IDs
                assert app.col_ns.id == "col-ns"
                assert app.col_types.id == "col-types"
                assert app.col_objects.id == "col-objects"
                
                # Check that header and footer exist
                header = app.query_one("#app-header-info", Static)
                assert header is not None

    @pytest.mark.asyncio
    async def test_app_handles_k8s_connection_error(self):
        """Test that app handles Kubernetes connection errors gracefully."""
        with patch('ktree.app.K8sManager', side_effect=Exception("Connection failed")):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                # App should still be running despite connection error
                assert app.connection_error is not None


class TestDataLoading:
    """Test data loading functionality."""

    @pytest.mark.asyncio
    async def test_loads_namespaces_on_startup(self, mock_k8s_manager, sample_namespaces):
        """Test that namespaces are loaded on app startup."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)  # Wait for async operations
                
                # Check that namespaces are loaded
                assert len(app.col_ns.items) == len(sample_namespaces)
                assert app.col_ns.items == sample_namespaces

    @pytest.mark.asyncio
    async def test_loads_object_types_on_namespace_selection(
        self, mock_k8s_manager, sample_namespaces, sample_object_types
    ):
        """Test that object types are loaded when namespace is selected."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        mock_k8s_manager.get_object_types.return_value = sample_object_types
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                
                # Simulate namespace selection
                message = Selected(app.col_ns, "default")
                app.on_browser_column_selected(message)
                await pilot.pause(0.3)
                
                # Check that object types are loaded
                assert len(app.col_types.items) > 0
                assert app.current_namespace == "default"

    @pytest.mark.asyncio
    async def test_loads_objects_on_type_selection(
        self, mock_k8s_manager, sample_namespaces, sample_object_types, sample_pods
    ):
        """Test that objects are loaded when object type is selected."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        mock_k8s_manager.get_object_types.return_value = sample_object_types
        mock_k8s_manager.get_objects.return_value = sample_pods
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
            
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                
                # Simulate type selection
                message = Selected(app.col_types, "Pods")
                app.on_browser_column_selected(message)
                await pilot.pause(0.3)
                
                # Check that objects are loaded
                assert len(app.col_objects.items) == len(sample_pods)
                assert app.current_object_type == "Pods"

    @pytest.mark.asyncio
    async def test_loads_details_on_object_selection(
        self, mock_k8s_manager, sample_yaml_details
    ):
        """Test that object details are loaded when object is selected."""
        mock_k8s_manager.get_details.return_value = sample_yaml_details
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
            app.current_object_type = "Pods"
            
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                
                # Simulate object selection
                message = Selected(app.col_objects, "test-pod")
                app.on_browser_column_selected(message)
                await pilot.pause(0.3)
                
                # Check that details are loaded
                details_widget = app.query_one("#details-content", Static)
                assert details_widget is not None
                # Check the content by rendering or checking the update was called
                details_text = str(details_widget.render())
                assert "test-pod" in details_text or "test-pod" in str(details_widget)

    @pytest.mark.asyncio
    async def test_handles_empty_namespace_list(self, mock_k8s_manager):
        """Test that app handles empty namespace list gracefully."""
        mock_k8s_manager.get_namespaces.return_value = []
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                
                # Check that empty list is handled
                assert len(app.col_ns.items) == 0

    @pytest.mark.asyncio
    async def test_handles_error_loading_namespaces(self, mock_k8s_manager):
        """Test that app handles errors when loading namespaces."""
        from ktree.k8s_manager import K8sManagerError
        mock_k8s_manager.get_namespaces.side_effect = K8sManagerError("Failed to fetch namespaces")
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                
                # App should handle error gracefully
                assert app.connection_error is not None or len(app.col_ns.items) == 0


class TestNavigation:
    """Test navigation functionality."""

    @pytest.mark.asyncio
    async def test_focus_left_moves_to_previous_column(self, mock_k8s_manager, sample_namespaces):
        """Test that focus_left() moves focus to the left column."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                
                # Start at column 0
                assert app.current_col_idx == 0
                
                # Move right first
                app.action_focus_right()
                await pilot.pause(0.1)
                assert app.current_col_idx == 1
                
                # Move left
                app.action_focus_left()
                await pilot.pause(0.1)
                assert app.current_col_idx == 0

    @pytest.mark.asyncio
    async def test_focus_right_moves_to_next_column(self, mock_k8s_manager, sample_namespaces):
        """Test that focus_right() moves focus to the next column."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                assert app.current_col_idx == 0
                assert app.current_col_idx == 1
                assert app.current_col_idx == 2

    @pytest.mark.asyncio
    async def test_focus_left_does_not_go_below_zero(self, mock_k8s_manager, sample_namespaces):
        """Test that focus_left() does not go below index 0."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                assert app.current_col_idx == 0
                assert app.current_col_idx == 0

    @pytest.mark.asyncio
    async def test_focus_right_does_not_exceed_max(self, mock_k8s_manager, sample_namespaces):
        """Test that focus_right() does not exceed maximum column index."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                assert app.current_col_idx == 2
                assert app.current_col_idx == 2

    @pytest.mark.asyncio
    async def test_focus_up_moves_selection_up(self, mock_k8s_manager, sample_namespaces):
        """Test that focus_up() moves selection up in current column."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                
                # Get the option list
                option_list = app.col_ns.query_one(HighlightedOptionList)
                assert option_list is not None
                
                # Set highlighted to index 2
                option_list.highlighted = 2
                await pilot.pause(0.1)
                
                # Move up
                app.action_focus_up()
                await pilot.pause(0.1)
                
                # Should be at index 1
                assert option_list.highlighted == 1

    @pytest.mark.asyncio
    async def test_focus_down_moves_selection_down(self, mock_k8s_manager, sample_namespaces):
        """Test that focus_down() moves selection down in current column."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                assert option_list is not None
                await pilot.pause(0.1)
                await pilot.pause(0.1)
                assert option_list.highlighted == 1


class TestCascadingSelection:
    """Test cascading selection functionality."""

    @pytest.mark.asyncio
    async def test_cascading_selection_on_startup(
        self, mock_k8s_manager, sample_namespaces, sample_object_types, sample_pods
    ):
        """Test that cascading selection works on startup."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        mock_k8s_manager.get_object_types.return_value = sample_object_types
        mock_k8s_manager.get_objects.return_value = sample_pods
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(1.0)  # Wait for cascading selection to complete
                assert len(app.col_ns.items) > 0

    @pytest.mark.asyncio
    async def test_selection_triggers_next_column_load(
        self, mock_k8s_manager, sample_namespaces, sample_object_types
    ):
        """Test that selecting an item triggers loading of next column."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        mock_k8s_manager.get_object_types.return_value = sample_object_types
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.3)
                assert app.current_namespace == "default"


class TestSearchFunctionality:
    """Test search/filter functionality."""

    @pytest.mark.asyncio
    async def test_toggle_search_shows_search_input(self, mock_k8s_manager, sample_namespaces):
        """Test that toggle_search() shows the search input."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.1)
                assert app.col_ns.search_active is True

    @pytest.mark.asyncio
    async def test_toggle_search_hides_search_input(self, mock_k8s_manager, sample_namespaces):
        """Test that toggle_search() hides the search input when active."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                assert app.col_ns.search_active is True
                assert app.col_ns.search_active is False

    @pytest.mark.asyncio
    async def test_search_filters_items(self, mock_k8s_manager, sample_namespaces):
        """Test that search input filters items in the column."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.1)
                await pilot.pause(0.1)
                assert all("default" in item.lower() for item in app.col_ns.filtered_items)


class TestRefreshFunctionality:
    """Test refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_reloads_namespaces(self, mock_k8s_manager, sample_namespaces):
        """Test that refresh() reloads namespaces."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                app.current_object_type = None
                await pilot.pause(0.3)
                assert mock_k8s_manager.get_namespaces.called

    @pytest.mark.asyncio
    async def test_refresh_reloads_object_types(
        self, mock_k8s_manager, sample_namespaces, sample_object_types
    ):
        """Test that refresh() reloads object types when namespace is selected."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        mock_k8s_manager.get_object_types.return_value = sample_object_types
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.3)
                assert mock_k8s_manager.get_object_types.called

    @pytest.mark.asyncio
    async def test_refresh_reloads_objects(
        self, mock_k8s_manager, sample_namespaces, sample_object_types, sample_pods
    ):
        """Test that refresh() reloads objects when type is selected."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        mock_k8s_manager.get_object_types.return_value = sample_object_types
        mock_k8s_manager.get_objects.return_value = sample_pods
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
            app.current_object_type = "Pods"
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.3)
                assert mock_k8s_manager.get_objects.call_args[0] == ("default", "Pods")


class TestLogsFunctionality:
    """Test logs viewing functionality."""

    @pytest.mark.asyncio
    async def test_view_logs_for_pod(self, mock_k8s_manager, sample_pods):
        """Test that view_logs() displays logs for selected pod."""
        mock_k8s_manager.get_logs.return_value = "test log line 1\ntest log line 2"
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
            app.current_object_type = "Pods"
            app.col_objects.set_items(sample_pods)
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                option_list.highlighted = 0
                await pilot.pause(0.3)
                assert mock_k8s_manager.get_logs.called

    @pytest.mark.asyncio
    async def test_view_logs_only_for_pods(self, mock_k8s_manager):
        """Test that view_logs() only works for Pods."""
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
            app.current_object_type = "Services"  # Not Pods
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.3)
                details_text = str(details_widget.render())
                assert "only available for Pods" in details_text.lower()


class TestExecFunctionality:
    """Test exec functionality."""

    @pytest.mark.asyncio
    async def test_exec_only_for_pods(self, mock_k8s_manager):
        """Test that exec() only works for Pods."""
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
            app.current_object_type = "Services"  # Not Pods
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.3)
                details_text = str(details_widget.render())
                assert "only available for Pods" in details_text.lower()

    @pytest.mark.asyncio
    async def test_exec_shows_message_for_pod(self, mock_k8s_manager, sample_pods):
        """Test that exec() shows message for selected pod."""
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_namespace = "default"
            app.current_object_type = "Pods"
            app.col_objects.set_items(sample_pods)
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                option_list.highlighted = 0
                await pilot.pause(0.3)
                details_text = str(details_widget.render())
                assert "exec" in details_text.lower()


class TestHeaderUpdates:
    """Test header update functionality."""

    @pytest.mark.asyncio
    async def test_header_shows_context_and_namespace(self, mock_k8s_manager, sample_namespaces):
        """Test that header displays context and namespace."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        mock_k8s_manager.get_current_context.return_value = "test-context"
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_context = "test-context"
            app.current_namespace = "default"
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.1)
                header_text = str(header.render())
                assert "default" in header_text

    @pytest.mark.asyncio
    async def test_header_updates_on_namespace_selection(
        self, mock_k8s_manager, sample_namespaces
    ):
        """Test that header updates when namespace is selected."""
        mock_k8s_manager.get_namespaces.return_value = sample_namespaces
        
        with patch('ktree.app.K8sManager', return_value=mock_k8s_manager):
            app = KTreeApp()
            app.current_context = "test-context"
        
            async with app.run_test() as pilot:
                await pilot.pause(0.5)
                await pilot.pause(0.3)
                assert app.current_namespace == "default"

