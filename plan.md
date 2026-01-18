# K8s browser

CLI full screen application that let's you browse a k8s cluster using directional arrows (left or h, right or l, up or k, down or j). 

It should be a tree based application. on the left the namespaces, next level will be the objects, next level the actual objects selected, then the logs, describe or even exec into container.

The application starts in the default current k8s profile/context but the namespace and object type can be selected even from the start using parameters.


# Layout

## Main Layout

### Fixed panels

1. First fixed Panel is the header with context and namespace (single line)
2. Second fixed panel is a container that contains 4 columns. The browsing columns are 3 (Namespace, Object Type [including CRDs], Objects). These columns have a fixed height (100% of the viewport height) and each column will have a width equal to the max length of the content in that column. The forth column will be used to display the details of the selected object (describe). 

At startup the items are loaded in the namespace column. The coursor should be placed on the first item. Because the first item has the cursor on top of it that triggers the loading on the second column. That means that the items in the Object type will be loaded. The movement to the next column will be triggered by the right key. If the left key is pressed that means that the previuos column is active.

Filtering on one of the first three columns is triggered by the press of filter key ?. If the enter key is pressed that means that the filter will be applied on the column items. If the ESC key is pressed the filter is switched off, the input is cleared and all the items in the column should be visible. if enter was pressed the column items should be filtered and the name of the column should be appended with an * asterics red.


3. Third panel in the footer with the the keybindings


## Help Overlay

The help overlay is a rectangle with the keybindings and will be placed on the bottom of the screen, centered horizontally, taking up 60% of the screen width. It can be toggled with the CTRL+B key.

## Cascading Selection Logic ✅

On startup, the application automatically triggers a "deep-dive" navigation experience:
1. The first namespace is selected and highlighted (with visual indicator ▶ and yellow background).
2. This triggers the loading of all object types for that namespace.
3. The first object type is then automatically selected and highlighted.
4. This triggers the loading of all objects for that type.
5. The first object is then automatically selected and highlighted.
6. Finally, this triggers the loading of the details (Describe) for that object.

This process ensures that the user is presented with data immediately upon opening the application without requiring any key presses.

## Next Steps

### Phase 1: Core Infrastructure ✅
- [x] Set up Python project structure
- [x] Install dependencies (kubernetes, textual, rich)
- [x] Create basic TUI skeleton with Textual
- [x] Basic app runs and displays placeholder

### Phase 2: Kubernetes Client Integration ✅
- [x] Initialize Kubernetes client using kubeconfig
- [x] Load default context/profile
- [x] Handle kubeconfig errors gracefully
- [x] Add support for context selection via parameter

### Phase 3: Tree Navigation UI ✅
- [x] Create tree widget for hierarchical navigation
- [x] Implement left panel for namespaces list
- [x] Implement middle panel for object types (pods, services, deployments, etc.)
- [x] Implement right panel for selected objects
- [x] Implement detail panel for object descriptions
- [x] Add keyboard navigation (h/j/k/l and arrow keys)
- [x] Handle navigation between panels

### Phase 4: Data Loading ✅
- [x] Fetch and display namespaces
- [x] Fetch and display object types per namespace
- [x] Fetch and display objects of selected type
- [x] Display object details (YAML/JSON view)
- [x] Add loading states and error handling
- [x] Implement cascading selection on startup
- [x] Async data loading with background workers
- [x] Loading indicators ("Loading data...")
- [x] Empty state indicators ("No items")
- [x] Disable columns when loading or empty

### Phase 5: Layout Implementation ✅
- [x] Implement Finder-like scrollable viewport layout
- [x] Configure column widths 
- [x] Implement dynamic column visibility based on selection
- [x] Handle navigation between columns with proper visibility
- [x] Fix Details panel at 60% width on the right

### Phase 6: Advanced Features ✅
- [x] Exec into containers functionality
- [x] Namespace filtering/selection at startup
- [x] Object type filtering via parameter
- [x] Search/filter functionality for search inputs
- [x] Refresh data capability
- [x] Logs viewing (optional)

### Phase 7: Polish ✅
- [x] Error messages and user feedback
- [x] Help screen with keybindings (CTRL+B)
- [x] Status bar with current context/namespace (single line header)
- [x] Color themes and styling
- [x] Visual highlighting on startup (custom HighlightedOptionList widget)
- [x] Dynamic column width adjustment based on content
- [x] Filter functionality with visual indicators (red asterisk)
- [x] Filter state persistence across namespace changes
- [x] Details panel with scrolling and filtering
- [x] Debug logging (optional via --debug flag)
- [x] Describe/Logs/Exec view switching (d/g/e keys)
- [x] Logs auto-scroll to bottom
- [x] Exec commands displayed in formatted boxes with CTRL+1-4 keybindings
- [x] Clipboard copy functionality for exec commands
- [x] Performance optimization for large clusters
  - [x] Async data loading using background workers
  - [x] Non-blocking UI during API calls
  - [x] Loading states ("Loading data...") for better UX
  - [x] Empty states ("No items") with disabled columns
  - [x] Responsive navigation even during data fetching