"""Functional tests for K8sManager."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from kubernetes.client.rest import ApiException
from ktree.k8s_manager import K8sManager, K8sManagerError


class TestK8sManagerInitialization:
    """Test K8sManager initialization."""

    def test_initializes_with_default_context(self):
        """Test that K8sManager initializes with default context."""
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            assert manager.context is None
            assert manager.config_loaded is True

    def test_initializes_with_specific_context(self):
        """Test that K8sManager initializes with specific context."""
        with patch('ktree.k8s_manager.config.load_kube_config') as mock_load, \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager(context="test-context")
            assert manager.context == "test-context"
            mock_load.assert_called_once_with(context="test-context")

    def test_raises_error_on_config_failure(self):
        """Test that K8sManager raises error on config load failure."""
        with patch('ktree.k8s_manager.config.load_kube_config', side_effect=Exception("Config error")):
            with pytest.raises(K8sManagerError) as exc_info:
                K8sManager()
            assert "Failed to load Kubernetes config" in str(exc_info.value)


class TestK8sManagerNamespaces:
    """Test namespace-related functionality."""

    def test_get_namespaces_returns_sorted_list(self):
        """Test that get_namespaces() returns sorted list of namespaces."""
        mock_core_v1 = MagicMock()
        mock_ns1 = MagicMock()
        mock_ns1.metadata.name = "zebra"
        mock_ns2 = MagicMock()
        mock_ns2.metadata.name = "alpha"
        mock_ns3 = MagicMock()
        mock_ns3.metadata.name = "beta"
        
        mock_list = MagicMock()
        mock_list.items = [mock_ns1, mock_ns2, mock_ns3]
        mock_core_v1.list_namespace.return_value = mock_list
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            namespaces = manager.get_namespaces()
            
            assert namespaces == ["alpha", "beta", "zebra"]
            assert namespaces == sorted(namespaces)

    def test_get_namespaces_handles_api_exception(self):
        """Test that get_namespaces() handles API exceptions."""
        mock_core_v1 = MagicMock()
        api_exception = ApiException(status=403, reason="Forbidden")
        mock_core_v1.list_namespace.side_effect = api_exception
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            with pytest.raises(K8sManagerError) as exc_info:
                manager.get_namespaces()
            assert "Failed to fetch namespaces" in str(exc_info.value)

    def test_get_namespaces_requires_initialized_client(self):
        """Test that get_namespaces() requires initialized client."""
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=None), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            manager.core_v1 = None
            
            with pytest.raises(K8sManagerError) as exc_info:
                manager.get_namespaces()
            assert "Kubernetes client not initialized" in str(exc_info.value)


class TestK8sManagerObjectTypes:
    """Test object type-related functionality."""

    def test_get_object_types_returns_standard_types(self):
        """Test that get_object_types() returns standard Kubernetes types."""
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api') as mock_crd_api:
            
            # Mock CRD list (empty)
            mock_crd_list = MagicMock()
            mock_crd_list.items = []
            mock_crd_api.return_value.list_custom_resource_definition.return_value = mock_crd_list
            
            manager = K8sManager()
            types = manager.get_object_types()
            
            # Check that standard types are included
            assert "Pods" in types
            assert "Services" in types
            assert "Deployments" in types
            assert "ConfigMaps" in types
            assert "Secrets" in types

    def test_get_object_types_includes_crds(self):
        """Test that get_object_types() includes Custom Resource Definitions."""
        mock_crd = MagicMock()
        mock_crd.spec.names.kind = "MyCustomResource"
        mock_crd_list = MagicMock()
        mock_crd_list.items = [mock_crd]
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api') as mock_crd_api:
            
            mock_crd_instance = MagicMock()
            mock_crd_instance.list_custom_resource_definition.return_value = mock_crd_list
            mock_crd_api.return_value = mock_crd_instance
            
            manager = K8sManager()
            manager.apiextensions_v1 = mock_crd_instance
            types = manager.get_object_types()
            
            # Check that CRD is included
            assert "MyCustomResource" in types


class TestK8sManagerObjects:
    """Test object-related functionality."""

    def test_get_objects_returns_pods(self):
        """Test that get_objects() returns pod names."""
        mock_core_v1 = MagicMock()
        mock_pod1 = MagicMock()
        mock_pod1.metadata.name = "pod-2"
        mock_pod2 = MagicMock()
        mock_pod2.metadata.name = "pod-1"
        
        mock_list = MagicMock()
        mock_list.items = [mock_pod1, mock_pod2]
        mock_core_v1.list_namespaced_pod.return_value = mock_list
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            pods = manager.get_objects("default", "Pods")
            
            assert pods == ["pod-1", "pod-2"]
            assert pods == sorted(pods)

    def test_get_objects_returns_services(self):
        """Test that get_objects() returns service names."""
        mock_core_v1 = MagicMock()
        mock_svc1 = MagicMock()
        mock_svc1.metadata.name = "svc-2"
        mock_svc2 = MagicMock()
        mock_svc2.metadata.name = "svc-1"
        
        mock_list = MagicMock()
        mock_list.items = [mock_svc1, mock_svc2]
        mock_core_v1.list_namespaced_service.return_value = mock_list
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            services = manager.get_objects("default", "Services")
            
            assert services == ["svc-1", "svc-2"]

    def test_get_objects_handles_empty_list(self):
        """Test that get_objects() handles empty object lists."""
        mock_core_v1 = MagicMock()
        mock_list = MagicMock()
        mock_list.items = []
        mock_core_v1.list_namespaced_pod.return_value = mock_list
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            pods = manager.get_objects("default", "Pods")
            
            assert pods == []

    def test_get_objects_handles_unsupported_type(self):
        """Test that get_objects() handles unsupported object types."""
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api') as mock_crd_api:
            
            # Mock empty CRD list
            mock_crd_list = MagicMock()
            mock_crd_list.items = []
            mock_crd_api.return_value.list_custom_resource_definition.return_value = mock_crd_list
            
            manager = K8sManager()
            objects = manager.get_objects("default", "UnsupportedType")
            
            # Should return empty list for unsupported types
            assert objects == []


class TestK8sManagerDetails:
    """Test object details functionality."""

    def test_get_details_returns_yaml(self):
        """Test that get_details() returns YAML representation."""
        mock_core_v1 = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_core_v1.read_namespaced_pod.return_value = mock_pod
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiClient') as mock_api_client:
            
            # Mock YAML serialization
            mock_client_instance = MagicMock()
            mock_client_instance.sanitize_for_serialization.return_value = {"metadata": {"name": "test-pod"}}
            mock_api_client.return_value = mock_client_instance
            
            manager = K8sManager()
            details = manager.get_details("default", "Pods", "test-pod")
            
            # Should return YAML string
            assert isinstance(details, str)
            assert "test-pod" in details or "name" in details.lower()

    def test_get_details_handles_api_exception(self):
        """Test that get_details() handles API exceptions."""
        mock_core_v1 = MagicMock()
        api_exception = ApiException(status=404, reason="Not Found")
        mock_core_v1.read_namespaced_pod.side_effect = api_exception
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            with pytest.raises(K8sManagerError) as exc_info:
                manager.get_details("default", "Pods", "nonexistent-pod")
            assert "Failed to fetch" in str(exc_info.value)


class TestK8sManagerLogs:
    """Test logs functionality."""

    def test_get_logs_returns_log_output(self):
        """Test that get_logs() returns log output."""
        mock_core_v1 = MagicMock()
        mock_core_v1.read_namespaced_pod_log.return_value = "log line 1\nlog line 2\nlog line 3"
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            logs = manager.get_logs("default", "test-pod")
            
            assert isinstance(logs, str)
            assert "log line 1" in logs
            assert "log line 2" in logs

    def test_get_logs_with_container(self):
        """Test that get_logs() works with container parameter."""
        mock_core_v1 = MagicMock()
        mock_core_v1.read_namespaced_pod_log.return_value = "container log"
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            logs = manager.get_logs("default", "test-pod", container="nginx")
            
            # Check that container parameter was passed
            mock_core_v1.read_namespaced_pod_log.assert_called_once()
            call_args = mock_core_v1.read_namespaced_pod_log.call_args
            assert call_args[1].get("container") == "nginx"

    def test_get_logs_handles_api_exception(self):
        """Test that get_logs() handles API exceptions."""
        mock_core_v1 = MagicMock()
        api_exception = ApiException(status=404, reason="Pod not found")
        mock_core_v1.read_namespaced_pod_log.side_effect = api_exception
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            with pytest.raises(K8sManagerError) as exc_info:
                manager.get_logs("default", "nonexistent-pod")
            assert "Failed to fetch logs" in str(exc_info.value)


class TestK8sManagerConnection:
    """Test connection functionality."""

    def test_test_connection_succeeds(self):
        """Test that test_connection() returns True on success."""
        mock_core_v1 = MagicMock()
        mock_list = MagicMock()
        mock_list.items = []
        mock_core_v1.list_namespace.return_value = mock_list
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            result = manager.test_connection()
            
            assert result is True

    def test_test_connection_fails_on_error(self):
        """Test that test_connection() returns False on error."""
        mock_core_v1 = MagicMock()
        mock_core_v1.list_namespace.side_effect = Exception("Connection failed")
        
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=mock_core_v1), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            result = manager.test_connection()
            
            assert result is False

    def test_get_current_context_returns_context_name(self):
        """Test that get_current_context() returns context name."""
        with patch('ktree.k8s_manager.config.load_kube_config'), \
             patch('ktree.k8s_manager.config.list_kube_config_contexts', return_value=([], {"name": "test-context"})), \
             patch('ktree.k8s_manager.client.CoreV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.AppsV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.BatchV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.NetworkingV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.RbacAuthorizationV1Api', return_value=MagicMock()), \
             patch('ktree.k8s_manager.client.CustomObjectsApi', return_value=MagicMock()), \
             patch('ktree.k8s_manager.ApiextensionsV1Api', return_value=MagicMock()):
            
            manager = K8sManager()
            context = manager.get_current_context()
            
            assert context == "test-context"

