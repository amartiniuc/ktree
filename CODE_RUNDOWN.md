# KTree Code Rundown - A Beginner's Guide

## Table of Contents
1. [What is KTree?](#what-is-ktree)
2. [Technologies Used](#technologies-used)
3. [Application Architecture](#application-architecture)
4. [Project Structure](#project-structure)
5. [How It Works - Step by Step](#how-it-works---step-by-step)
6. [Key Components Explained](#key-components-explained)
7. [Data Flow](#data-flow)
8. [Key Programming Concepts](#key-programming-concepts)
9. [Understanding the Code](#understanding-the-code)

---

## What is KTree?

KTree is a **Terminal User Interface (TUI)** application that lets you browse Kubernetes clusters in a Finder-like interface. Instead of using `kubectl` commands, you can visually navigate through:

- **Namespaces** (like folders)
- **Object Types** (like Pod, Service, Deployment, etc.)
- **Objects** (actual instances like "my-app-pod")
- **Details** (YAML configuration of the selected object)

Think of it like macOS Finder, but for Kubernetes resources!

---

## Technologies Used

### 1. **Textual** (Python TUI Framework)
- **What it is**: A framework for building terminal-based user interfaces
- **Why we use it**: Provides widgets, layouts, event handling, and styling for terminal apps
- **Key features we use**:
  - Widgets (buttons, lists, containers)
  - CSS-like styling
  - Event-driven programming
  - Message passing between components

### 2. **Kubernetes Python Client**
- **What it is**: Official Python library to interact with Kubernetes clusters
- **Why we use it**: Connects to your cluster and fetches data (namespaces, pods, etc.)
- **Key features we use**:
  - Reading cluster configuration from `~/.kube/config`
  - Listing namespaces, pods, services, etc.
  - Getting detailed YAML for objects

### 3. **Rich** (Text Formatting)
- **What it is**: Library for beautiful terminal output
- **Why we use it**: Syntax highlighting for YAML in the details panel

### 4. **Python Standard Library**
- `asyncio`: For asynchronous operations (non-blocking code)
- `argparse`: For command-line argument parsing
- `os`, `sys`: For file operations and system interactions

---

## Application Architecture

KTree follows a **component-based architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│              KTreeApp (Main App)                │
│  - Handles UI layout                            │
│  - Manages navigation                           │
│  - Coordinates between components               │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                 │
┌──────▼──────┐  ┌──────▼──────────┐
│ K8sManager  │  │  BrowserColumn   │
│             │  │  (3 instances)   │
│ - Connects  │  │                  │
│   to K8s    │  │ - Namespaces     │
│ - Fetches   │  │ - Object Types   │
│   data      │  │ - Objects        │
└─────────────┘  └──────────────────┘
```

### High-Level Flow:
1. **App starts** → Initializes K8s connection
2. **UI renders** → Three columns appear
3. **Data loads** → First namespace is fetched
4. **User navigates** → Selecting items triggers cascading data loads
5. **Details show** → YAML appears in the right panel

---

## Project Structure

```
ktree/
├── ktree/                    # Main package
│   ├── __init__.py          # Package marker
│   ├── main.py              # Entry point (CLI argument parsing)
│   ├── app.py               # Main application class
│   ├── k8s_manager.py       # Kubernetes API wrapper
│   ├── styles.css           # UI styling
│   └── widgets/             # Custom UI components
│       ├── column.py        # BrowserColumn widget
│       ├── help.py          # Help overlay widget
│       └── custom_option_list.py  # Enhanced list widget
├── tests/                   # Test files
└── requirements.txt         # Dependencies
```

---

## How It Works - Step by Step

### Step 1: Application Startup (`main.py`)

```python
def run():
    parser = argparse.ArgumentParser(...)
    args = parser.parse_args()
    
    app = KTreeApp(
        initial_context=args.context,
        initial_namespace=args.namespace,
        initial_type=args.type
    )
    app.run()
```

**What happens:**
1. Parse command-line arguments (context, namespace, type)
2. Create the main app instance
3. Start the Textual application loop

### Step 2: App Initialization (`app.py` - `__init__`)

```python
def __init__(self, initial_context=None, initial_namespace=None, initial_type=None):
    super().__init__()
    _cleanup_log_files()  # Clear old log files
    
    # Initialize Kubernetes connection
    self.k8s = K8sManager(context=self.initial_context)
    
    # Store state
    self.columns = []
    self.current_col_idx = 0
```

**What happens:**
1. Clean up log files from previous runs
2. Connect to Kubernetes cluster
3. Initialize state variables (current column, selected items, etc.)

### Step 3: UI Composition (`app.py` - `compose`)

```python
def compose(self) -> ComposeResult:
    yield Header(show_clock=True)
    yield Static(self.get_header_text(), id="app-header-info")
    
    with Horizontal(id="main-container"):
        with Horizontal(id="browser-viewport"):
            # Three columns for browsing
            yield self.col_ns      # Namespaces
            yield self.col_types   # Object Types
            yield self.col_objects # Objects
        
        with Vertical(id="details-panel"):
            yield Static("Select an object...", id="details-content")
    
    yield Footer()
```

**What happens:**
1. Create header with clock
2. Create info bar showing context/namespace
3. Create main container with:
   - Left side: Three browsing columns (horizontal scrollable)
   - Right side: Details panel (60% width)
4. Create footer with keybindings

**Key Concept**: `yield` is used to add widgets to the UI. Textual builds the UI tree from these yields.

### Step 4: Data Loading (`app.py` - `on_ready`)

```python
async def on_ready(self) -> None:
    namespaces = self.k8s.get_namespaces()
    self.col_ns.set_items(namespaces)
    
    # Ensure first item is selected and highlighted
    async def ensure_first_selected():
        await asyncio.sleep(0.5)
        target_list.focus()
        target_list.highlighted_index = 0
```

**What happens:**
1. Fetch all namespaces from Kubernetes
2. Populate the first column with namespace names
3. Automatically select and highlight the first namespace
4. This triggers the "cascading selection" (see below)

### Step 5: Cascading Selection

When a namespace is selected:
1. **Namespace selected** → Load object types (Pod, Service, etc.)
2. **Object type selected** → Load objects of that type
3. **Object selected** → Load YAML details

This happens automatically through **message passing** (explained below).

---

## Key Components Explained

### 1. KTreeApp (`app.py`)

**Purpose**: Main application class that orchestrates everything.

**Key Responsibilities:**
- **Layout Management**: Defines the UI structure
- **Navigation**: Handles moving between columns (left/right)
- **Data Coordination**: Receives selection messages and triggers data loading
- **Keybindings**: Maps keyboard keys to actions

**Important Methods:**
- `compose()`: Defines the UI structure
- `on_ready()`: Called when app is fully loaded
- `on_browser_column_selected()`: Handles when user selects an item
- `action_*()`: Methods that respond to key presses

### 2. K8sManager (`k8s_manager.py`)

**Purpose**: Wrapper around Kubernetes Python client.

**Key Responsibilities:**
- **Connection**: Loads kubeconfig and connects to cluster
- **Data Fetching**: Gets namespaces, object types, objects, and details
- **Error Handling**: Catches and reports Kubernetes API errors

**Important Methods:**
- `get_namespaces()`: Returns list of namespace names
- `get_object_types()`: Returns list of Kubernetes resource types
- `get_objects(namespace, type)`: Returns objects of a type in a namespace
- `get_details(namespace, type, name)`: Returns YAML for a specific object

**How it works:**
```python
# Example: Getting namespaces
def get_namespaces(self):
    ns_list = self.core_v1.list_namespace()
    return sorted([ns.metadata.name for ns in ns_list.items])
```

The `core_v1` is a Kubernetes API client that talks to your cluster.

### 3. BrowserColumn (`widgets/column.py`)

**Purpose**: A reusable column widget that displays a list of items.

**Structure:**
```
BrowserColumn
├── Static (title)          # Column header
├── SearchInput (hidden)    # Search box (shown when / is pressed)
└── HighlightedOptionList   # The actual list of items
```

**Key Features:**
- **Search**: Press `/` or `?` to filter items
- **Selection**: Press Enter or click to select an item
- **Navigation**: Arrow keys move up/down
- **Message Sending**: Posts `Selected` message when item is chosen

**Important Methods:**
- `set_items(items)`: Populates the list
- `toggle_search()`: Shows/hides search input
- `on_option_list_option_selected()`: Called when user selects an item

**Key Concept - Messages:**
```python
class Selected(Message):
    def __init__(self, column, item):
        self.column = column
        self.item = item

# When item is selected:
self.post_message(self.Selected(self, "default"))
```

This message is sent to the parent app, which then loads the next level of data.

### 4. SearchInput (`widgets/column.py`)

**Purpose**: Custom search input with special key handling.

**Key Features:**
- **ENTER**: Applies filter and focuses list
- **ESC**: Clears filter and restores full list

**How it works:**
```python
async def action_apply_filter_and_focus_list(self):
    self.add_class("hidden")  # Hide search box
    column.search_active = False
    item_list.focus()  # Return focus to list
```

### 5. HighlightedOptionList (`widgets/custom_option_list.py`)

**Purpose**: Enhanced list widget that ensures highlights are visible on startup.

**Problem it solves**: Textual's default OptionList only shows highlights after user interaction. This custom version ensures the first item is highlighted immediately.

**Key Features:**
- Overrides `render_line()` to force highlight rendering
- Adds visual indicator (▶) for highlighted items
- Clears render caches to force fresh rendering

### 6. HelpOverlay (`widgets/help.py`)

**Purpose**: Help screen showing keybindings.

**Features:**
- Appears at bottom of screen (60% width, centered)
- Toggled with CTRL+B
- Non-interactive (doesn't block main app)

---

## Data Flow

Understanding how data moves through the application:

### 1. Initial Load

```
User starts app
    ↓
KTreeApp.__init__()
    ↓
K8sManager connects to cluster
    ↓
KTreeApp.on_ready()
    ↓
K8sManager.get_namespaces()
    ↓
BrowserColumn.set_items(namespaces)
    ↓
First namespace auto-selected
    ↓
BrowserColumn posts Selected message
    ↓
KTreeApp.on_browser_column_selected()
    ↓
K8sManager.get_object_types()
    ↓
Second column populated
    ↓
(Process repeats for object types → objects → details)
```

### 2. User Selection Flow

```
User presses Enter on "default" namespace
    ↓
HighlightedOptionList emits OptionSelected event
    ↓
BrowserColumn.on_option_list_option_selected()
    ↓
BrowserColumn.post_message(Selected(column, "default"))
    ↓
KTreeApp.on_browser_column_selected(message)
    ↓
if message.column.id == "col-namespaces":
    self.k8s.current_namespace = "default"
    types = self.k8s.get_object_types()
    self.col_types.set_items(types)
```

### 3. Search Flow

```
User presses "/"
    ↓
KTreeApp.action_toggle_search()
    ↓
BrowserColumn.toggle_search()
    ↓
SearchInput becomes visible and focused
    ↓
User types "kube"
    ↓
SearchInput.on_input_changed()
    ↓
Filter items containing "kube"
    ↓
BrowserColumn.update_list(filtered_items)
    ↓
List shows only matching items
```

---

## Key Programming Concepts

### 1. **Object-Oriented Programming (OOP)**

Classes are blueprints for creating objects:

```python
class BrowserColumn(Vertical):
    def __init__(self, title):
        self.title = title
        self.all_items = []
```

- `BrowserColumn` is a class
- `Vertical` is the parent class (inheritance)
- `__init__` is the constructor (runs when object is created)
- `self` refers to the instance

### 2. **Inheritance**

Child classes inherit from parent classes:

```python
class BrowserColumn(Vertical):  # Inherits from Vertical
    # Gets all Vertical's methods and properties
    # Can override or extend them
```

### 3. **Event-Driven Programming**

Instead of constantly checking for changes, the app responds to events:

```python
def on_option_list_option_selected(self, event):
    # This runs automatically when an option is selected
    # We don't need to poll or check - Textual calls this for us
```

### 4. **Message Passing**

Components communicate through messages:

```python
# Component A sends a message
self.post_message(self.Selected(self, "default"))

# Component B receives it
def on_browser_column_selected(self, message):
    # Handle the message
```

This is like passing notes between components - they don't need to know about each other directly.

### 5. **Async/Await**

For non-blocking operations:

```python
async def on_ready(self):
    await asyncio.sleep(0.5)  # Wait without blocking the UI
```

`async` functions can be paused and resumed, allowing the UI to stay responsive.

### 6. **CSS Styling**

Textual uses CSS-like styling:

```css
.browser-column {
    width: auto;
    border-right: solid #1e293b;
}
```

This is similar to web CSS but for terminal UIs.

### 7. **Widget Composition**

Building complex UIs from simple parts:

```python
def compose(self):
    yield Header()           # Simple widget
    yield BrowserColumn()    # Complex widget (contains other widgets)
    yield Footer()          # Simple widget
```

Each widget can contain other widgets, creating a tree structure.

---

## Understanding the Code

### Example 1: How Navigation Works

```python
def action_focus_right(self) -> None:
    if self.current_col_idx < len(self.columns) - 1:
        self.current_col_idx += 1
        target = self.columns[self.current_col_idx].query_one("#item-list")
        target.focus()
        self.scroll_to_column()
```

**Breaking it down:**
1. `action_focus_right`: Called when user presses `l` or `→`
2. `if self.current_col_idx < len(self.columns) - 1`: Check if we can move right
3. `self.current_col_idx += 1`: Move to next column index
4. `query_one("#item-list")`: Find the list widget in that column
5. `target.focus()`: Give it keyboard focus
6. `scroll_to_column()`: Scroll viewport to show the column

### Example 2: How Search Filtering Works

```python
def on_input_changed(self, event: Input.Changed) -> None:
    if event.input.id == "search-input":
        search_term = event.value.lower()
        filtered_items = [item for item in self.all_items 
                         if search_term in item.lower()]
        self.update_list(filtered_items)
```

**Breaking it down:**
1. `on_input_changed`: Called automatically when user types
2. `event.value`: The text in the search box
3. `[item for item in ... if ...]`: List comprehension - filters items
4. `if search_term in item.lower()`: Case-insensitive matching
5. `self.update_list()`: Updates the displayed list

### Example 3: How Details Are Loaded

```python
def on_browser_column_selected(self, message: BrowserColumn.Selected):
    if message.column.id == "col-objects":
        self.current_object = message.item
        details = self.k8s.get_details(
            self.k8s.current_namespace,
            self.current_type,
            self.current_object
        )
        syntax = Syntax(details, "yaml", theme="monokai")
        self.query_one("#details-content", Static).update(syntax)
```

**Breaking it down:**
1. Message received when object is selected
2. Check which column sent it (`col-objects`)
3. Fetch YAML details from Kubernetes
4. Create syntax-highlighted YAML
5. Update the details panel widget

---

## Common Patterns in the Code

### Pattern 1: Querying Widgets

```python
# Find a widget by ID
self.query_one("#item-list")

# Find multiple widgets
self.query(".browser-column")

# Check if widget exists
if self.query("#help-overlay"):
    self.query_one("#help-overlay").remove()
```

### Pattern 2: Updating Widgets

```python
# Update text content
static_widget.update("New text")

# Update with Rich renderable
static_widget.update(Syntax(yaml_text, "yaml"))

# Add/remove CSS classes
widget.add_class("hidden")
widget.remove_class("hidden")
```

### Pattern 3: Message Handling

```python
# Sending a message
self.post_message(self.Selected(self, item))

# Receiving a message (method name must match pattern)
def on_browser_column_selected(self, message):
    # Handle message
```

### Pattern 4: Async Operations

```python
# Define async function
async def do_something():
    await asyncio.sleep(1)
    # Do work

# Run it in background
self.run_worker(do_something())
```

---

## Tips for Understanding the Code

1. **Start with `main.py`**: This is where execution begins
2. **Follow the flow**: Trace how data moves from user action → UI update
3. **Read method names**: They're descriptive (e.g., `on_ready`, `action_focus_right`)
4. **Check the CSS**: `styles.css` shows how things look
5. **Use print debugging**: Add `print()` statements to see what's happening
6. **Read Textual docs**: Understanding Textual helps understand this code

---

## Extending the Application

### Adding a New Feature: Export to File

```python
# In app.py, add a new binding
BINDINGS = [
    # ... existing bindings ...
    ("e", "export_details", "Export"),
]

# Add the action method
def action_export_details(self):
    if self.current_object:
        details = self.k8s.get_details(...)
        with open("export.yaml", "w") as f:
            f.write(details)
        self.notify("Exported to export.yaml")
```

### Adding a New Column

```python
# In compose()
self.col_new = BrowserColumn("New Column", id="col-new")
yield self.col_new
self.columns.append(self.col_new)

# Handle its selection
def on_browser_column_selected(self, message):
    # ... existing code ...
    elif message.column.id == "col-new":
        # Handle new column
```

---

## Summary

KTree is a well-structured TUI application that:

1. **Uses Textual** for the UI framework
2. **Uses Kubernetes client** for cluster interaction
3. **Follows component-based architecture** with clear separation
4. **Uses message passing** for component communication
5. **Implements cascading selection** for automatic data loading
6. **Provides search functionality** for filtering lists
7. **Shows YAML details** with syntax highlighting

The code is organized, readable, and follows Python best practices. Each component has a single responsibility, making it easier to understand and modify.

---

## Further Reading

- [Textual Documentation](https://textual.textualize.io/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Python Async/Await Guide](https://docs.python.org/3/library/asyncio.html)

---

*This guide was created to help beginners understand how KTree works. If you have questions or find errors, please contribute improvements!*

