"""Pytest configuration and fixtures for KTree tests."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List
from kubernetes.client.rest import ApiException
from ktree.k8s_manager import K8sManager


@pytest.fixture
def mock_k8s_client():
    """Create a mock Kubernetes client."""
    mock_client = MagicMock()
    
    # Mock namespace list
    mock_ns_item = MagicMock()
    mock_ns_item.metadata.name = "default"
    mock_ns_list = MagicMock()
    mock_ns_list.items = [mock_ns_item]
    
    # Mock pod list
    mock_pod_item = MagicMock()
    mock_pod_item.metadata.name = "test-pod"
    mock_pod_list = MagicMock()
    mock_pod_list.items = [mock_pod_item]
    
    # Mock service list
    mock_svc_item = MagicMock()
    mock_svc_item.metadata.name = "test-service"
    mock_svc_list = MagicMock()
    mock_svc_list.items = [mock_svc_item]
    
    # Mock pod object for details
    mock_pod = MagicMock()
    mock_pod.metadata.name = "test-pod"
    mock_pod.metadata.namespace = "default"
    
    # Configure mock methods
    mock_client.core_v1.list_namespace.return_value = mock_ns_list
    mock_client.core_v1.list_namespaced_pod.return_value = mock_pod_list
    mock_client.core_v1.list_namespaced_service.return_value = mock_svc_list
    mock_client.core_v1.read_namespaced_pod.return_value = mock_pod
    mock_client.core_v1.read_namespaced_pod_log.return_value = "test log line 1\ntest log line 2"
    
    return mock_client


@pytest.fixture
def mock_k8s_manager(mock_k8s_client):
    """Create a mock K8sManager."""
    manager = MagicMock(spec=K8sManager)
    
    # Set up default return values
    manager.get_namespaces.return_value = ["default", "kube-system"]
    manager.get_object_types.return_value = ["Pods", "Services", "Deployments"]
    manager.get_objects.return_value = ["pod-1", "pod-2"]
    manager.get_details.return_value = "apiVersion: v1\nkind: Pod"
    manager.get_logs.return_value = "log line 1\nlog line 2"
    manager.get_current_context.return_value = "test-context"
    manager.test_connection.return_value = True
    manager.current_namespace = None
    manager.context = None
    manager.config_loaded = True
    
    # Set up API clients as mocks
    manager.core_v1 = mock_k8s_client.core_v1
    manager.apps_v1 = MagicMock()
    manager.batch_v1 = MagicMock()
    manager.networking_v1 = MagicMock()
    manager.rbac_authorization_v1 = MagicMock()
    manager.custom_objects = MagicMock()
    manager.apiextensions_v1 = MagicMock()
    manager.apiextensions_v1.list_custom_resource_definition.return_value = MagicMock(items=[])
    
    return manager


@pytest.fixture
def sample_namespaces() -> List[str]:
    """Return a list of sample namespace names."""
    return ["default", "kube-system", "kube-public", "production", "staging"]


@pytest.fixture
def sample_object_types() -> List[str]:
    """Return a list of sample object types."""
    return [
        "Pods",
        "Services",
        "Deployments",
        "ReplicaSets",
        "StatefulSets",
        "DaemonSets",
        "Jobs",
        "CronJobs",
        "ConfigMaps",
        "Secrets",
    ]


@pytest.fixture
def sample_pods() -> List[str]:
    """Return a list of sample pod names."""
    return ["pod-1", "pod-2", "pod-3", "test-pod", "nginx-pod"]


@pytest.fixture
def sample_services() -> List[str]:
    """Return a list of sample service names."""
    return ["service-1", "service-2", "nginx-service", "api-service"]


@pytest.fixture
def sample_yaml_details() -> str:
    """Return sample YAML details for an object."""
    return """apiVersion: v1
kind: Pod
metadata:
  name: test-pod
  namespace: default
spec:
  containers:
  - name: nginx
    image: nginx:latest
status:
  phase: Running
"""

