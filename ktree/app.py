"""Main Textual application for KTree."""

import logging
import platform
import subprocess
from typing import Optional, List
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Footer, Static
from textual import on
from ktree.k8s_manager import K8sManager, K8sManagerError
from ktree.widgets.column import BrowserColumn, Selected
from ktree.widgets.custom_option_list import HighlightedOptionList
from ktree.widgets.details_panel import DetailsPanel
from ktree.widgets.help import HelpOverlay

debug_logger = logging.getLogger('debug')


class KTreeApp(App):
    """A Textual application for browsing Kubernetes clusters."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    #app-header-info {
        height: 3;
        text-align: center;
        background: $panel;
        border-bottom: solid $primary;
        padding: 0 1;
    }
    
    #main-container {
        height: 1fr;
    }
    
    #browser-viewport {
        height: 100%;
        width: auto;
        overflow-x: auto;
        overflow-y: hidden;
    }
    
    BrowserColumn {
        min-width: 15;
        height: 100%;
    }
    
    #details-panel {
        width: 1fr;
        height: 100%;
        min-width: 20;
    }
    
    #details-content {
        padding: 1;
        height: 1fr;
        overflow-y: auto;
    }
    
    #error {
        content-align: center middle;
        text-style: bold;
        color: $error;
        padding: 2;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "focus_left", "Left"),
        ("l", "focus_right", "Right"),
        ("j", "focus_down", "Down"),
        ("k", "focus_up", "Up"),
        ("left", "focus_left", "Left"),
        ("right", "focus_right", "Right"),
        ("down", "focus_down", "Down"),
        ("up", "focus_up", "Up"),
        ("r", "refresh", "Refresh"),
        ("/", "toggle_search", "Search"),
        ("?", "toggle_search", "Search"),
        ("d", "view_describe", "Describe"),
        ("g", "view_logs", "View Logs"),
        ("e", "exec_container", "Exec"),
        ("ctrl+b", "toggle_help", "Help"),
        ("ctrl+1", "copy_command_1", "Copy Cmd 1"),
        ("ctrl+2", "copy_command_2", "Copy Cmd 2"),
        ("ctrl+3", "copy_command_3", "Copy Cmd 3"),
        ("ctrl+4", "copy_command_4", "Copy Cmd 4"),
    ]

    def __init__(
        self,
        initial_context: Optional[str] = None,
        initial_namespace: Optional[str] = None,
        initial_type: Optional[str] = None,
    ):
        """
        Initialize the KTree application.

        Args:
            initial_context: Optional Kubernetes context name to use.
            initial_namespace: Optional namespace to select at startup.
            initial_type: Optional object type to select at startup.
        """
        super().__init__()
        self.initial_context = initial_context
        self.initial_namespace = initial_namespace
        self.initial_type = initial_type
        self.k8s: Optional[K8sManager] = None
        self.connection_error: Optional[str] = None
        self.current_context: Optional[str] = None
        self.current_namespace: Optional[str] = None
        self.current_object_type: Optional[str] = None
        self.current_view: str = "describe"  # "describe", "logs", or "exec"
        self.describe_content: Optional[str] = None  # Store the describe content to restore later
        self.current_pod_name: Optional[str] = None  # Store the current pod name for exec
        self._exec_commands: List[str] = []  # Store all exec commands for copying
        
        # Column widgets
        self.col_ns: Optional[BrowserColumn] = None
        self.col_types: Optional[BrowserColumn] = None
        self.col_objects: Optional[BrowserColumn] = None
        self.details_panel: Optional[DetailsPanel] = None
        self.help_overlay: Optional[HelpOverlay] = None
        self.columns: List[BrowserColumn] = []
        self.current_col_idx = 0
        self.max_col_idx = 3  # 0=namespaces, 1=types, 2=objects, 3=details

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Static("", id="app-header-info")
        
        with Horizontal(id="main-container"):
            with Horizontal(id="browser-viewport"):
                self.col_ns = BrowserColumn("Namespaces", id="col-ns")
                yield self.col_ns
                self.columns.append(self.col_ns)
                
                self.col_types = BrowserColumn("Object Types", id="col-types")
                yield self.col_types
                self.columns.append(self.col_types)
                
                self.col_objects = BrowserColumn("Objects", id="col-objects")
                yield self.col_objects
                self.columns.append(self.col_objects)
            
            self.details_panel = DetailsPanel(id="details-panel")
            yield self.details_panel
        
        yield Footer()
        
        self.help_overlay = HelpOverlay(id="help-overlay")
        yield self.help_overlay

    def on_mount(self) -> None:
        """Called when the app is mounted (after compose)."""
        debug_logger.info("ACTION: App mounted, initializing K8s connection")
        self._initialize_k8s()

    def _initialize_k8s(self) -> None:
        """Initialize Kubernetes client connection."""
        debug_logger.info(f"LOAD: Initializing K8s connection (context={self.initial_context})")
        try:
            self.k8s = K8sManager(context=self.initial_context)
            self.current_context = self.k8s.get_current_context()
            debug_logger.info(f"LOAD: K8s client initialized, current context: {self.current_context}")

            # Test connection
            if not self.k8s.test_connection():
                debug_logger.error("LOAD: Failed to connect to Kubernetes cluster")
                self.connection_error = "Failed to connect to Kubernetes cluster"
                self._update_error_display()
            else:
                debug_logger.info("LOAD: K8s connection test successful")
                # Update header and load initial data
                self._update_header()
                self._load_initial_data()

        except (K8sManagerError, Exception) as e:
            debug_logger.error(f"LOAD: Error initializing K8s: {e}")
            self.connection_error = str(e)
            self._update_error_display()

    def _update_header(self) -> None:
        """Update the header with context and namespace info."""
        header = self.query_one("#app-header-info", Static)
        context_text = self.current_context or "Unknown"
        namespace_text = self.current_namespace or "All Namespaces"
        header.update(f"Context: {context_text} | Namespace: {namespace_text}")

    def _load_initial_data(self) -> None:
        """Load initial data (namespaces) into the first column."""
        if not self.k8s:
            return
        
        debug_logger.info("LOAD: Loading initial data (namespaces)")
        # Show loading state
        self.col_ns.set_loading(True)
        if self.details_panel:
            self.details_panel.update_content("Loading namespaces...")
        
        # Run blocking K8s call in background worker
        def load_namespaces():
            try:
                namespaces = self.k8s.get_namespaces()
                # Update UI from worker thread using call_from_thread
                self.call_from_thread(self._on_namespaces_loaded, namespaces)
            except K8sManagerError as e:
                debug_logger.error(f"LOAD: Error loading initial data: {e}")
                self.call_from_thread(self._on_namespaces_error, str(e))
        
        self.run_worker(load_namespaces, thread=True, exclusive=False)
    
    def _on_namespaces_loaded(self, namespaces: List[str]) -> None:
        """Handle namespaces loaded callback."""
        if namespaces is None:
            self.connection_error = "Failed to load namespaces"
            self._update_error_display()
            return
        
        debug_logger.info(f"LOAD: Loaded {len(namespaces)} namespaces: {namespaces[:5]}{'...' if len(namespaces) > 5 else ''}")
        self.col_ns.set_items(namespaces)
        
        # Handle initial namespace selection
        if self.initial_namespace and self.initial_namespace in namespaces:
            debug_logger.info(f"LOAD: Selecting initial namespace: {self.initial_namespace}")
            # Find and select the initial namespace
            ns_idx = namespaces.index(self.initial_namespace)
            option_list = self.col_ns.query_one(HighlightedOptionList)
            if option_list:
                option_list.highlighted = ns_idx
                # Trigger selection to load object types
                self.current_namespace = self.initial_namespace
                self._update_header()
                self._load_object_types_for_namespace(self.initial_namespace)
        else:
            # If no initial namespace specified, manually trigger selection of first namespace
            # This ensures object types are loaded even if the message from set_items doesn't fire
            if len(namespaces) > 0:
                debug_logger.info(f"LOAD: Auto-selecting first namespace: {namespaces[0]}")
                # Use a small delay to ensure the widget is ready
                self.set_timer(0.2, lambda: self.on_browser_column_selected(Selected(self.col_ns, namespaces[0])))
            
            # Focus on the first column
            self._focus_column(0)
    
    def _on_namespaces_error(self, error: str) -> None:
        """Handle namespaces loading error."""
        self.connection_error = error
        self._update_error_display()

    def _load_object_types_for_namespace(self, namespace: str) -> None:
        """Load object types for a namespace and optionally select initial type."""
        if not self.k8s:
            return
        
        debug_logger.info(f"LOAD: Loading object types for namespace: {namespace}")
        # Show loading state
        self.col_types.set_loading(True)
        
        # Run blocking K8s call in background worker
        def load_object_types():
            try:
                object_types = self.k8s.get_object_types()
                self.call_from_thread(self._on_object_types_loaded, namespace, object_types)
            except K8sManagerError as e:
                debug_logger.error(f"LOAD: Error loading object types: {e}")
                self.call_from_thread(self._on_object_types_error)
        
        self.run_worker(load_object_types, thread=True, exclusive=False)
    
    def _on_object_types_loaded(self, namespace: str, object_types: List[str]) -> None:
        """Handle object types loaded callback."""
        debug_logger.info(f"LOAD: Loaded {len(object_types)} object types: {object_types[:5]}{'...' if len(object_types) > 5 else ''}")
        self.col_types.set_items(object_types)
        
        # Handle initial type selection (only during initial load)
        if hasattr(self, 'initial_type') and self.initial_type and self.initial_type in object_types:
            debug_logger.info(f"LOAD: Selecting initial type: {self.initial_type}")
            type_idx = object_types.index(self.initial_type)
            option_list = self.col_types.query_one(HighlightedOptionList)
            if option_list:
                option_list.highlighted = type_idx
                # Trigger selection to load objects
                self.current_object_type = self.initial_type
                self._load_objects_for_type(namespace, self.initial_type)
    
    def _on_object_types_error(self) -> None:
        """Handle object types loading error."""
        if self.details_panel:
            self.details_panel.update_content("Error loading object types")

    def _load_objects_for_type(self, namespace: str, object_type: str) -> None:
        """Load objects for a type and optionally select first object."""
        if not self.k8s:
            return
        
        debug_logger.info(f"LOAD: Loading objects for type '{object_type}' in namespace '{namespace}'")
        # Show loading state
        self.col_objects.set_loading(True)
        
        # Run blocking K8s call in background worker
        def load_objects():
            try:
                objects = self.k8s.get_objects(namespace, object_type)
                self.call_from_thread(self._on_objects_loaded, namespace, object_type, objects)
            except K8sManagerError as e:
                debug_logger.error(f"LOAD: Error loading objects: {e}")
                self.call_from_thread(self._on_objects_error, object_type)
        
        self.run_worker(load_objects, thread=True, exclusive=False)
    
    def _on_objects_loaded(self, namespace: str, object_type: str, objects: List[str]) -> None:
        """Handle objects loaded callback."""
        debug_logger.info(f"LOAD: Loaded {len(objects)} objects of type '{object_type}': {objects[:5]}{'...' if len(objects) > 5 else ''}")
        self.col_objects.set_items(objects)
    
    def _on_objects_loaded_from_selection(self, object_type: str, objects: List[str]) -> None:
        """Handle objects loaded from column selection."""
        debug_logger.info(f"LOAD: Loaded {len(objects)} objects of type '{object_type}' in namespace '{self.current_namespace}'")
        if objects:
            self.col_objects.set_items(objects)
        else:
            debug_logger.info(f"LOAD: No objects found for type '{object_type}' in namespace '{self.current_namespace}'")
            # No objects found - show message
            self.col_objects.set_items([])
            if self.details_panel:
                self.details_panel.update_content(f"No {object_type} found in namespace: {self.current_namespace}")
    
    def _on_objects_error(self, object_type: str) -> None:
        """Handle objects loading error."""
        if self.details_panel:
            self.details_panel.update_content(f"Error loading objects: {object_type}")
    
    def _on_objects_error_from_selection(self, object_type: str) -> None:
        """Handle objects loading error from column selection."""
        # Error loading objects - show error
        self.col_objects.set_items([])
        if self.details_panel:
            self.details_panel.update_content(f"Error loading {object_type} in namespace: {self.current_namespace}")
    
    def _on_details_loaded(self, object_type: str, item: str, yaml_details: str) -> None:
        """Handle details loaded callback."""
        debug_logger.info(f"LOAD: Loaded details for {object_type}/{item} (size={len(yaml_details)} chars)")
        if self.details_panel:
            self.describe_content = yaml_details
            self.current_view = "describe"
            self.details_panel.update_content(yaml_details)
    
    def _on_details_error(self, object_type: str, item: str) -> None:
        """Handle details loading error."""
        if self.details_panel:
            self.details_panel.update_content(f"Error loading details for {object_type}/{item}")
    
    def _on_objects_refreshed(self, objects: List[str]) -> None:
        """Handle objects refreshed callback."""
        debug_logger.info(f"LOAD: Refreshed {len(objects)} objects")
        self.col_objects.set_items(objects)
    
    def _on_objects_refresh_error(self) -> None:
        """Handle objects refresh error."""
        if self.details_panel:
            self.details_panel.update_content("Error refreshing objects")
    
    def _on_object_types_refreshed(self, object_types: List[str]) -> None:
        """Handle object types refreshed callback."""
        debug_logger.info(f"LOAD: Refreshed {len(object_types)} object types")
        self.col_types.set_items(object_types)
    
    def _on_object_types_refresh_error(self) -> None:
        """Handle object types refresh error."""
        if self.details_panel:
            self.details_panel.update_content("Error refreshing object types")
    
    def _on_namespaces_refreshed(self, namespaces: List[str]) -> None:
        """Handle namespaces refreshed callback."""
        debug_logger.info(f"LOAD: Refreshed {len(namespaces)} namespaces")
        self.col_ns.set_items(namespaces)
    
    def _on_namespaces_refresh_error(self) -> None:
        """Handle namespaces refresh error."""
        if self.details_panel:
            self.details_panel.update_content("Error refreshing namespaces")
    
    def _on_logs_loaded(self, pod_name: str, logs: str) -> None:
        """Handle logs loaded callback."""
        debug_logger.info(f"LOAD: Loaded logs for pod '{pod_name}' (size={len(logs)} chars)")
        if self.details_panel:
            self.current_view = "logs"
            self.details_panel.update_content(f"Logs for pod: {pod_name}\n\n{logs}", scroll_to_bottom=True)
    
    def _on_logs_error(self, pod_name: str) -> None:
        """Handle logs loading error."""
        if self.details_panel:
            self.details_panel.update_content(f"Error loading logs for pod: {pod_name}")

    def _update_error_display(self) -> None:
        """Update the display to show error message."""
        # For now, we'll show errors in the details panel
        if self.details_panel and self.connection_error:
            self.details_panel.update_content(
                f"✗ Connection Error\n\n{self.connection_error}\n\nPress 'q' to quit"
            )

    def _focus_column(self, idx: int) -> None:
        """
        Focus on a specific column and scroll to make it visible.

        Args:
            idx: Column index to focus.
        """
        if 0 <= idx < len(self.columns):
            self.current_col_idx = idx
            column = self.columns[idx]
            
            # Scroll to make the focused column visible
            self._scroll_to_column(column)
            
            # Focus the option list
            option_list = column.query_one(HighlightedOptionList)
            if option_list:
                option_list.focus()

    def _focus_details_panel(self) -> None:
        """Focus on the details panel."""
        debug_logger.info(f"ACTION: Focusing details panel")
        self.current_col_idx = self.max_col_idx
        if self.details_panel:
            # Focus the details panel widget itself
            self.details_panel.focus()
            debug_logger.info(f"ACTION: Details panel focused, current_col_idx={self.current_col_idx}")

    def _scroll_to_column(self, column: BrowserColumn) -> None:
        """
        Scroll the viewport to make the specified column visible.

        Args:
            column: The column widget to scroll to.
        """
        viewport = self.query_one("#browser-viewport")
        if viewport and hasattr(viewport, 'scroll_to_widget'):
            try:
                # Scroll the column into view
                viewport.scroll_to_widget(column, animate=False)
            except Exception:
                # If scroll_to_widget doesn't work, try alternative approach
                pass

    @on(Selected)
    def on_browser_column_selected(self, message: Selected) -> None:
        """
        Handle selection in a browser column.

        Args:
            message: Selected message from a column.
        """
        if not self.k8s:
            return

        column_id = message.column.id
        item = message.item
        debug_logger.info(f"ACTION: Column selected - column={column_id}, item={item}")

        try:
            if column_id == "col-ns":
                # Namespace selected - load object types
                debug_logger.info(f"LOAD: Namespace selected: {item}")
                self.current_namespace = item
                self._update_header()
                
                # Show loading state
                self.col_types.set_loading(True)
                if self.details_panel:
                    self.details_panel.update_content(f"Loading object types for namespace: {item}...")
                
                # Clear objects column
                self.col_objects.set_items([])
                self.current_object_type = None
                self.describe_content = None
                self.current_view = "describe"
                # Update title to default (no Logs/Exec options)
                if self.details_panel:
                    self.details_panel.update_title(is_pod=False)
                
                # Load object types in background worker
                def load_object_types():
                    try:
                        object_types = self.k8s.get_object_types()
                        self.call_from_thread(self._on_object_types_loaded, item, object_types)
                    except K8sManagerError as e:
                        debug_logger.error(f"LOAD: Error loading object types: {e}")
                        self.call_from_thread(self._on_object_types_error)
                
                self.run_worker(load_object_types, thread=True, exclusive=False)
                # Keep focus on the current column (namespaces)
                # User can press 'l' or right arrow to move to types column
                
            elif column_id == "col-types":
                # Object type selected - load objects
                if not self.current_namespace:
                    return
                
                debug_logger.info(f"LOAD: Object type selected: {item} in namespace '{self.current_namespace}'")
                self.current_object_type = item
                self.describe_content = None
                self.current_view = "describe"
                
                # Update title based on object type (show Logs/Exec only for Pods)
                if self.details_panel:
                    self.details_panel.update_title(is_pod=(item == "Pods"))
                    self.details_panel.update_content(f"Loading {item} in namespace: {self.current_namespace}...")
                
                # Show loading state
                self.col_objects.set_loading(True)
                
                # Load objects of this type in background worker
                def load_objects():
                    try:
                        objects = self.k8s.get_objects(self.current_namespace, item)
                        self.call_from_thread(self._on_objects_loaded_from_selection, item, objects)
                    except Exception as e:
                        debug_logger.error(f"LOAD: Error loading objects: {e}")
                        self.call_from_thread(self._on_objects_error_from_selection, item)
                
                self.run_worker(load_objects, thread=True, exclusive=False)
                # Keep focus on the current column (types)
                # User can press 'l' or right arrow to move to objects column
                
            elif column_id == "col-objects":
                # Object selected - load details
                if not self.current_namespace or not self.current_object_type:
                    return
                
                debug_logger.info(f"LOAD: Object selected: {item} (type={self.current_object_type}, namespace={self.current_namespace})")
                object_type = self.current_object_type
                
                # Store pod name if this is a Pod
                if object_type == "Pods":
                    self.current_pod_name = item
                else:
                    self.current_pod_name = None
                
                # Update title based on object type (show Logs/Exec only for Pods)
                if self.details_panel:
                    self.details_panel.update_title(is_pod=(object_type == "Pods"))
                    self.details_panel.update_content(f"Loading details for {object_type}/{item}...")
                
                # Load object details in background worker
                def load_details():
                    try:
                        yaml_details = self.k8s.get_details(self.current_namespace, object_type, item)
                        self.call_from_thread(self._on_details_loaded, object_type, item, yaml_details)
                    except K8sManagerError as e:
                        debug_logger.error(f"LOAD: Error loading details for {object_type}/{item}: {e}")
                        self.call_from_thread(self._on_details_error, object_type, item)
                
                self.run_worker(load_details, thread=True, exclusive=False)
                        
        except K8sManagerError as e:
            debug_logger.error(f"LOAD: Error in column selection handler: {e}")
            # Show error in details panel
            if self.details_panel:
                self.details_panel.update_content(f"Error: {str(e)}")

    def action_focus_left(self) -> None:
        """Move focus to the left column."""
        debug_logger.info(f"ACTION: focus_left (current_col_idx={self.current_col_idx})")
        if self.current_col_idx > 0:
            self._focus_column(self.current_col_idx - 1)

    def action_focus_right(self) -> None:
        """Move focus to the right column."""
        debug_logger.info(f"ACTION: focus_right (current_col_idx={self.current_col_idx})")
        if self.current_col_idx < len(self.columns) - 1:
            # Moving between browser columns
            self._focus_column(self.current_col_idx + 1)
        elif self.current_col_idx == len(self.columns) - 1:
            # Moving from objects column (last browser column) to details panel
            self._focus_details_panel()

    def action_focus_up(self) -> None:
        """Move selection up in current column or scroll up in details panel."""
        debug_logger.info(f"ACTION: focus_up (current_col_idx={self.current_col_idx})")
        if self.current_col_idx < len(self.columns):
            column = self.columns[self.current_col_idx]
            option_list = column.query_one(HighlightedOptionList)
            if option_list:
                option_list.action_cursor_up()
                # Trigger selection on highlight change for cascading
                self._trigger_selection_from_highlight(column, option_list)
        elif self.current_col_idx == self.max_col_idx and self.details_panel:
            # Scroll up in details panel
            self.details_panel.action_scroll_up()

    def action_focus_down(self) -> None:
        """Move selection down in current column or scroll down in details panel."""
        debug_logger.info(f"ACTION: focus_down (current_col_idx={self.current_col_idx})")
        if self.current_col_idx < len(self.columns):
            column = self.columns[self.current_col_idx]
            option_list = column.query_one(HighlightedOptionList)
            if option_list:
                option_list.action_cursor_down()
                # Trigger selection on highlight change for cascading
                self._trigger_selection_from_highlight(column, option_list)
        elif self.current_col_idx == self.max_col_idx and self.details_panel:
            # Scroll down in details panel
            self.details_panel.action_scroll_down()

    def _trigger_selection_from_highlight(self, column: BrowserColumn, option_list: HighlightedOptionList) -> None:
        """Trigger selection based on current highlight for cascading."""
        # Use a small timer to ensure the highlight is fully updated
        def trigger():
            highlighted = option_list.highlighted
            debug_logger.info(f"ACTION: _trigger_selection_from_highlight - column={column.id}, highlighted={highlighted}, filtered_items_len={len(column.filtered_items)}")
            if highlighted is not None and highlighted < len(column.filtered_items):
                selected_item = column.filtered_items[highlighted]
                debug_logger.info(f"ACTION: Triggering selection for item: {selected_item}")
                self.on_browser_column_selected(Selected(column, selected_item))
            else:
                debug_logger.warning(f"ACTION: Cannot trigger selection - highlighted={highlighted}, filtered_items_len={len(column.filtered_items)}")
        
        # Use a small delay to ensure highlight is updated
        self.set_timer(0.05, trigger)

    def action_refresh(self) -> None:
        """Refresh the current data."""
        debug_logger.info(f"ACTION: refresh (namespace={self.current_namespace}, type={self.current_object_type})")
        if not self.k8s:
            return
        
        # Refresh based on current state
        if self.current_namespace and self.current_object_type:
            # Refresh objects
            debug_logger.info(f"LOAD: Refreshing objects for type '{self.current_object_type}' in namespace '{self.current_namespace}'")
            self.col_objects.set_loading(True)
            
            def load_objects():
                try:
                    objects = self.k8s.get_objects(self.current_namespace, self.current_object_type)
                    self.call_from_thread(self._on_objects_refreshed, objects)
                except K8sManagerError as e:
                    debug_logger.error(f"LOAD: Error refreshing objects: {e}")
                    self.call_from_thread(self._on_objects_refresh_error)
            
            self.run_worker(load_objects, thread=True, exclusive=False)
        elif self.current_namespace:
            # Refresh object types
            debug_logger.info(f"LOAD: Refreshing object types for namespace '{self.current_namespace}'")
            self.col_types.set_loading(True)
            
            def load_object_types():
                try:
                    object_types = self.k8s.get_object_types()
                    self.call_from_thread(self._on_object_types_refreshed, object_types)
                except K8sManagerError as e:
                    debug_logger.error(f"LOAD: Error refreshing object types: {e}")
                    self.call_from_thread(self._on_object_types_refresh_error)
            
            self.run_worker(load_object_types, thread=True, exclusive=False)
        else:
            # Refresh namespaces
            debug_logger.info("LOAD: Refreshing namespaces")
            self.col_ns.set_loading(True)
            
            def load_namespaces():
                try:
                    namespaces = self.k8s.get_namespaces()
                    self.call_from_thread(self._on_namespaces_refreshed, namespaces)
                except K8sManagerError as e:
                    debug_logger.error(f"LOAD: Error refreshing namespaces: {e}")
                    self.call_from_thread(self._on_namespaces_refresh_error)
            
            self.run_worker(load_namespaces, thread=True, exclusive=False)

    def action_toggle_search(self) -> None:
        """Toggle search in the current column or details panel."""
        debug_logger.info(f"ACTION: toggle_search (current_col_idx={self.current_col_idx})")
        if self.current_col_idx < len(self.columns):
            column = self.columns[self.current_col_idx]
            column.action_toggle_search()
        elif self.current_col_idx == self.max_col_idx and self.details_panel:
            self.details_panel.action_toggle_search()

    def action_view_describe(self) -> None:
        """Switch back to describe view from logs or exec."""
        debug_logger.info("ACTION: view_describe")
        if self.describe_content and self.details_panel:
            self.current_view = "describe"
            # Note: Keep current_pod_name in case user wants to exec again
            self.details_panel.update_content(self.describe_content)
            debug_logger.info("ACTION: Switched back to describe view")

    def action_view_logs(self) -> None:
        """View logs for the selected pod."""
        debug_logger.info("ACTION: view_logs")
        if not self.k8s or not self.current_namespace:
            return
        
        # Check if we have a pod selected
        if self.current_object_type != "Pods":
            debug_logger.info("ACTION: view_logs - not a pod, ignoring")
            if self.details_panel:
                self.details_panel.update_content("Logs are only available for Pods. Please select a Pod first.")
            return
        
        # Get the selected pod name
        option_list = self.col_objects.query_one(HighlightedOptionList)
        if not option_list or option_list.highlighted is None:
            return
        
        # Get the selected pod name from filtered items
        if option_list.highlighted is not None and option_list.highlighted < len(self.col_objects.filtered_items):
            pod_name = self.col_objects.filtered_items[option_list.highlighted]
        else:
            return
        
        debug_logger.info(f"LOAD: Loading logs for pod '{pod_name}' in namespace '{self.current_namespace}'")
        # Show loading state
        if self.details_panel:
            self.details_panel.update_content(f"Loading logs for pod: {pod_name}...")
        
        # Load logs in background worker
        def load_logs():
            try:
                logs = self.k8s.get_logs(self.current_namespace, pod_name)
                self.call_from_thread(self._on_logs_loaded, pod_name, logs)
            except K8sManagerError as e:
                debug_logger.error(f"LOAD: Error loading logs: {e}")
                self.call_from_thread(self._on_logs_error, pod_name)
        
        self.run_worker(load_logs, thread=True, exclusive=False)

    def action_exec_container(self) -> None:
        """Show exec commands for the selected pod container."""
        debug_logger.info("ACTION: exec_container")
        if not self.k8s or not self.current_namespace:
            return
        
        # Check if we have a pod selected
        if self.current_object_type != "Pods":
            debug_logger.info("ACTION: exec_container - not a pod, ignoring")
            if self.details_panel:
                self.details_panel.update_content("Exec is only available for Pods. Please select a Pod first.")
                self.current_view = "describe"
            return
        
        # Get the selected pod name
        option_list = self.col_objects.query_one(HighlightedOptionList)
        if not option_list or option_list.highlighted is None:
            return
        
        try:
            # Get the selected pod name from filtered items
            if option_list.highlighted is not None and option_list.highlighted < len(self.col_objects.filtered_items):
                pod_name = self.col_objects.filtered_items[option_list.highlighted]
            else:
                return
            debug_logger.info(f"ACTION: exec_container - pod '{pod_name}' in namespace '{self.current_namespace}'")
            self.current_pod_name = pod_name
            if self.details_panel:
                self.current_view = "exec"
                context_part = f" --context {self.current_context}" if self.current_context else ""
                
                # Build all exec commands
                shells = [
                    ("/bin/sh", "most common"),
                    ("/bin/bash", "full Linux images"),
                    ("/bin/ash", "Alpine Linux"),
                    ("/bin/zsh", "some images"),
                ]
                
                self._exec_commands = []
                for shell, description in shells:
                    cmd = f"kubectl exec -it {pod_name} -n {self.current_namespace}{context_part} -- {shell}"
                    self._exec_commands.append(cmd)
                
                # Format the commands in boxes with keybindings
                content_lines = [
                    f"[bold]Exec commands for pod: {pod_name}[/bold]\n",
                    "Press CTRL+1, CTRL+2, CTRL+3, or CTRL+4 to copy a command to clipboard.\n",
                    "Press 'd' to return to describe view.\n\n",
                ]
                
                # Use a fixed reasonable width that fits in the details panel
                # Details panel is typically 60% of screen width, so use ~70 chars
                box_width = 70
                
                for idx, (cmd, (shell, description)) in enumerate(zip(self._exec_commands, shells), 1):
                    header_text = f"CTRL+{idx}"
                    # Top border: "┌─ CTRL+X ─" + dashes + "┐"
                    header_part = f"┌─ {header_text} ─"
                    header_len = len(header_part) - 1  # -1 because we'll add "┐" separately
                    dashes_needed = max(1, box_width - header_len - 1)  # -1 for "┐"
                    top_border = f"[bold cyan]{header_part}{'─' * dashes_needed}┐[/bold cyan]"
                    bottom_border = f"[bold cyan]└{'─' * (box_width - 2)}┘[/bold cyan]"
                    
                    content_lines.append(top_border)
                    # Description line - pad to box width
                    desc_line = f"[bold cyan]│[/bold cyan] [dim]# {description}[/dim]"
                    content_lines.append(desc_line)
                    # Command line - wrap if needed
                    cmd_line = f"[bold cyan]│[/bold cyan] {cmd}"
                    # If command is too long, wrap it
                    if len(cmd) > box_width - 4:  # -4 for "│ " and " │"
                        # Split command into multiple lines
                        cmd_parts = []
                        remaining = cmd
                        while len(remaining) > box_width - 4:
                            # Try to break at spaces
                            break_point = box_width - 4
                            if ' ' in remaining[:break_point]:
                                # Find last space before break point
                                break_point = remaining.rfind(' ', 0, box_width - 4)
                            cmd_parts.append(remaining[:break_point])
                            remaining = remaining[break_point:].lstrip()
                        if remaining:
                            cmd_parts.append(remaining)
                        
                        for i, part in enumerate(cmd_parts):
                            if i == 0:
                                content_lines.append(f"[bold cyan]│[/bold cyan] {part}")
                            else:
                                content_lines.append(f"[bold cyan]│[/bold cyan]   {part}")  # Indent continuation
                    else:
                        content_lines.append(cmd_line)
                    content_lines.append(bottom_border)
                    content_lines.append("")  # Empty line for spacing
                
                self.details_panel.update_content("\n".join(content_lines))
        except Exception as e:
            debug_logger.error(f"ACTION: exec_container error: {e}")
            if self.details_panel:
                self.details_panel.update_content(f"Error: {str(e)}")

    def _copy_command_by_index(self, index: int) -> None:
        """
        Copy an exec command to the system clipboard by index.
        
        Args:
            index: The 1-based index of the command to copy.
        """
        if not self._exec_commands or index < 1 or index > len(self._exec_commands):
            debug_logger.info(f"ACTION: copy_command - invalid index {index}")
            return
        
        command = self._exec_commands[index - 1]  # Convert to 0-based
        debug_logger.info(f"ACTION: copy_command_{index} - copying: {command}")
        success = self._copy_to_clipboard(command)
        if success:
            # Show toast notification
            self.notify(f"Command {index} copied to clipboard!", severity="information", timeout=3)
        else:
            self.notify("Failed to copy to clipboard", severity="error", timeout=3)
    
    def action_copy_command_1(self) -> None:
        """Copy the first exec command to clipboard."""
        self._copy_command_by_index(1)
    
    def action_copy_command_2(self) -> None:
        """Copy the second exec command to clipboard."""
        self._copy_command_by_index(2)
    
    def action_copy_command_3(self) -> None:
        """Copy the third exec command to clipboard."""
        self._copy_command_by_index(3)
    
    def action_copy_command_4(self) -> None:
        """Copy the fourth exec command to clipboard."""
        self._copy_command_by_index(4)
    
    def _copy_to_clipboard(self, text: str) -> bool:
        """
        Copy text to the system clipboard using platform-specific commands.
        
        Args:
            text: The text to copy to clipboard.
        
        Returns:
            True if copy was successful, False otherwise.
        """
        system = platform.system()
        try:
            if system == "Darwin":  # macOS
                subprocess.run(["pbcopy"], input=text.encode(), check=True)
                debug_logger.info("ACTION: Copied to clipboard using pbcopy (macOS)")
                return True
            elif system == "Linux":
                # Try xclip first, then xsel
                try:
                    subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
                    debug_logger.info("ACTION: Copied to clipboard using xclip (Linux)")
                    return True
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode(), check=True)
                        debug_logger.info("ACTION: Copied to clipboard using xsel (Linux)")
                        return True
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        debug_logger.warning("ACTION: No clipboard utility found on Linux (xclip or xsel required)")
                        return False
            elif system == "Windows":
                subprocess.run(["clip"], input=text.encode(), check=True)
                debug_logger.info("ACTION: Copied to clipboard using clip (Windows)")
                return True
            else:
                debug_logger.warning(f"ACTION: Unsupported platform for clipboard: {system}")
                return False
        except Exception as e:
            debug_logger.error(f"ACTION: Error copying to clipboard: {e}")
            return False

    def action_toggle_help(self) -> None:
        """Toggle the help overlay."""
        debug_logger.info("ACTION: toggle_help")
        if self.help_overlay:
            self.help_overlay.toggle()

    def action_quit(self) -> None:
        """Action to quit the application."""
        debug_logger.info("ACTION: quit")
        self.exit()
    
    def on_key(self, event) -> None:
        """Handle all key presses and log them."""
        key_str = event.key
        if event.character:
            key_str = f"{key_str} (char: {event.character})"
        debug_logger.info(f"KEY_PRESS: {key_str}")
        # Event will continue to be handled by other handlers automatically

