# KTree Functional Tests

This directory contains functional tests for the KTree application.

## Test Structure

- `conftest.py` - Pytest configuration and shared fixtures
- `test_app_functional.py` - Functional tests for the main KTreeApp
- `test_widgets_functional.py` - Functional tests for custom widgets
- `test_k8s_manager_functional.py` - Functional tests for K8sManager

## Running Tests

### Run All Tests

```bash
# From project root
pytest tests/

# Or with verbose output
pytest tests/ -v

# Or with coverage
pytest tests/ --cov=ktree --cov-report=html
```

### Run Specific Test Files

```bash
# Test only the app
pytest tests/test_app_functional.py

# Test only widgets
pytest tests/test_widgets_functional.py

# Test only K8s manager
pytest tests/test_k8s_manager_functional.py
```

### Run Specific Test Classes or Methods

```bash
# Run a specific test class
pytest tests/test_app_functional.py::TestAppInitialization

# Run a specific test method
pytest tests/test_app_functional.py::TestAppInitialization::test_app_initializes_with_defaults
```

### Run Tests with Markers

```bash
# Run only async tests
pytest tests/ -m asyncio
```

## Test Coverage

The functional tests cover:

### Application Tests (`test_app_functional.py`)
- ✅ App initialization with various parameters
- ✅ Widget composition and creation
- ✅ Data loading (namespaces, object types, objects, details)
- ✅ Navigation (left/right/up/down)
- ✅ Cascading selection on startup
- ✅ Search/filter functionality
- ✅ Refresh functionality
- ✅ Logs viewing
- ✅ Exec functionality
- ✅ Header updates
- ✅ Error handling

### Widget Tests (`test_widgets_functional.py`)
- ✅ BrowserColumn initialization
- ✅ Item population and filtering
- ✅ Search toggle and filtering
- ✅ Case-insensitive search
- ✅ Message posting on selection
- ✅ Column width adjustment
- ✅ HighlightedOptionList highlighting
- ✅ List navigation
- ✅ Option clearing

### K8sManager Tests (`test_k8s_manager_functional.py`)
- ✅ Manager initialization
- ✅ Namespace fetching
- ✅ Object type listing (including CRDs)
- ✅ Object fetching
- ✅ Object details retrieval
- ✅ Logs retrieval
- ✅ Connection testing
- ✅ Error handling

## Test Fixtures

The `conftest.py` file provides several useful fixtures:

- `mock_k8s_client` - Mock Kubernetes client
- `mock_k8s_manager` - Mock K8sManager instance
- `sample_namespaces` - Sample namespace list
- `sample_object_types` - Sample object type list
- `sample_pods` - Sample pod names
- `sample_services` - Sample service names
- `sample_yaml_details` - Sample YAML output

## Writing New Tests

When writing new tests:

1. **Use fixtures** from `conftest.py` when possible
2. **Mock external dependencies** (Kubernetes API, file system, etc.)
3. **Use `@pytest.mark.asyncio`** for async tests
4. **Use `app.run_test()`** for Textual app/widget tests
5. **Add appropriate pauses** (`await pilot.pause()`) for async operations
6. **Follow naming conventions**: `test_<functionality>_<expected_behavior>`

### Example Test

```python
@pytest.mark.asyncio
async def test_example_functionality(mock_k8s_manager, sample_namespaces):
    """Test that example functionality works correctly."""
    mock_k8s_manager.get_namespaces.return_value = sample_namespaces
    
    app = KTreeApp()
    app.k8s = mock_k8s_manager
    
    async with app.run_test() as pilot:
        await pilot.pause(0.5)
        
        # Perform test actions
        app.action_some_action()
        await pilot.pause(0.1)
        
        # Assert expected behavior
        assert app.some_state == expected_value
```

## Notes

- Tests use mocks for Kubernetes API calls, so no actual cluster connection is required
- Textual widgets must be tested within an app context using `app.run_test()`
- Some tests may require timing adjustments (`pilot.pause()` duration) based on system performance
- All tests should be deterministic and not depend on external state

## Continuous Integration

These tests are designed to run in CI/CD pipelines. They:
- Don't require a Kubernetes cluster
- Use mocks for all external dependencies
- Are fast and deterministic
- Provide good coverage of application functionality

