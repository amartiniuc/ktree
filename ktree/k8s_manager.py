"""Kubernetes client manager for KTree."""

import logging
import os
from typing import Optional, List, Dict, Any
import yaml
from kubernetes import config, client
from kubernetes.client.rest import ApiException
from kubernetes.client import ApiextensionsV1Api

debug_logger = logging.getLogger('debug')


class K8sManagerError(Exception):
    """Base exception for K8sManager errors."""

    pass


class K8sManager:
    """Manages Kubernetes client connection and API operations."""

    def __init__(self, context: Optional[str] = None):
        """
        Initialize Kubernetes client.

        Args:
            context: Optional Kubernetes context name. If None, uses default context.

        Raises:
            K8sManagerError: If kubeconfig cannot be loaded or context is invalid.
        """
        self.context = context
        self.config_loaded = False
        self.core_v1: Optional[client.CoreV1Api] = None
        self.apps_v1: Optional[client.AppsV1Api] = None
        self.batch_v1: Optional[client.BatchV1Api] = None
        self.networking_v1: Optional[client.NetworkingV1Api] = None
        self.rbac_authorization_v1: Optional[client.RbacAuthorizationV1Api] = None
        self.custom_objects: Optional[client.CustomObjectsApi] = None
        self.apiextensions_v1: Optional[ApiextensionsV1Api] = None

        try:
            self._load_config()
        except Exception as e:
            raise K8sManagerError(f"Failed to load Kubernetes config: {e}") from e

    def _load_config(self) -> None:
        """Load Kubernetes configuration from kubeconfig."""
        debug_logger.info(f"LOAD: Loading K8s config (context={self.context})")
        try:
            # Try to load from default location (~/.kube/config)
            if self.context:
                config.load_kube_config(context=self.context)
            else:
                config.load_kube_config()
            debug_logger.info("LOAD: K8s config loaded successfully")

            # Initialize API clients
            self.core_v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.batch_v1 = client.BatchV1Api()
            self.networking_v1 = client.NetworkingV1Api()
            self.rbac_authorization_v1 = client.RbacAuthorizationV1Api()
            self.custom_objects = client.CustomObjectsApi()
            self.apiextensions_v1 = ApiextensionsV1Api()

            self.config_loaded = True

        except config.ConfigException as e:
            raise K8sManagerError(
                f"Kubernetes config error: {e}\n"
                "Make sure you have a valid kubeconfig file at ~/.kube/config"
            ) from e
        except Exception as e:
            raise K8sManagerError(f"Unexpected error loading config: {e}") from e

    def get_current_context(self) -> Optional[str]:
        """
        Get the current Kubernetes context name.

        Returns:
            Current context name, or None if not available.
        """
        try:
            contexts, active_context = config.list_kube_config_contexts()
            if active_context:
                return active_context.get("name")
            return None
        except Exception:
            return None

    def test_connection(self) -> bool:
        """
        Test the connection to the Kubernetes cluster.

        Returns:
            True if connection is successful, False otherwise.
        """
        if not self.config_loaded or not self.core_v1:
            return False

        try:
            # Try to list namespaces as a simple connection test
            # This is more reliable than get_api_versions()
            self.core_v1.list_namespace(limit=1)
            return True
        except Exception:
            return False

    def get_namespaces(self) -> List[str]:
        """
        Get list of all namespace names.

        Returns:
            Sorted list of namespace names.

        Raises:
            K8sManagerError: If unable to fetch namespaces.
        """
        debug_logger.info("LOAD: Fetching namespaces from K8s API")
        if not self.core_v1:
            raise K8sManagerError("Kubernetes client not initialized")

        try:
            ns_list = self.core_v1.list_namespace()
            namespaces = sorted([ns.metadata.name for ns in ns_list.items])
            debug_logger.info(f"LOAD: Fetched {len(namespaces)} namespaces from K8s API")
            return namespaces
        except ApiException as e:
            raise K8sManagerError(
                f"Failed to fetch namespaces: {e.reason} (Status: {e.status})"
            ) from e
        except Exception as e:
            raise K8sManagerError(f"Unexpected error fetching namespaces: {e}") from e

    def get_object_types(self) -> List[str]:
        """
        Get list of standard Kubernetes object types including CRDs.

        Returns:
            List of object type names (Pods, Services, Deployments, CRDs, etc.).
        """
        debug_logger.info("LOAD: Fetching object types (including CRDs)")
        # Standard Kubernetes resource types
        standard_types = [
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
            "PersistentVolumes",
            "PersistentVolumeClaims",
            "Ingresses",
            "ServiceAccounts",
            "Roles",
            "RoleBindings",
            "ClusterRoles",
            "ClusterRoleBindings",
        ]
        
        # Get Custom Resource Definitions (CRDs)
        crd_types = []
        if self.apiextensions_v1:
            try:
                # Get all CRDs from the cluster
                debug_logger.info("LOAD: Fetching CRDs from K8s API")
                crds = self.apiextensions_v1.list_custom_resource_definition()
                for crd in crds.items:
                    # Get the kind (singular form) from the CRD spec
                    if crd.spec and crd.spec.names and crd.spec.names.kind:
                        crd_types.append(crd.spec.names.kind)
                debug_logger.info(f"LOAD: Found {len(crd_types)} CRDs")
            except Exception as e:
                debug_logger.warning(f"LOAD: Error fetching CRDs: {e}")
                # If we can't fetch CRDs, just continue without them
                pass
        
        # Combine and sort
        all_types = standard_types + sorted(crd_types)
        debug_logger.info(f"LOAD: Total object types: {len(all_types)} (standard: {len(standard_types)}, CRDs: {len(crd_types)})")
        return all_types

    def get_objects(self, namespace: str, object_type: str) -> List[str]:
        """
        Get list of objects of a specific type in a namespace.

        Args:
            namespace: Namespace name.
            object_type: Type of object (e.g., "Pods", "Services").

        Returns:
            Sorted list of object names.

        Raises:
            K8sManagerError: If unable to fetch objects.
        """
        debug_logger.info(f"LOAD: Fetching objects of type '{object_type}' in namespace '{namespace}' from K8s API")
        if not self.core_v1:
            raise K8sManagerError("Kubernetes client not initialized")

        try:
            object_names: List[str] = []

            # Map object types to their API methods
            type_mapping: Dict[str, Any] = {
                "Pods": (self.core_v1, "list_namespaced_pod", namespace),
                "Services": (self.core_v1, "list_namespaced_service", namespace),
                "ConfigMaps": (self.core_v1, "list_namespaced_config_map", namespace),
                "Secrets": (self.core_v1, "list_namespaced_secret", namespace),
                "ServiceAccounts": (self.core_v1, "list_namespaced_service_account", namespace),
                "PersistentVolumeClaims": (
                    self.core_v1,
                    "list_namespaced_persistent_volume_claim",
                    namespace,
                ),
                "Deployments": (self.apps_v1, "list_namespaced_deployment", namespace),
                "ReplicaSets": (self.apps_v1, "list_namespaced_replica_set", namespace),
                "StatefulSets": (self.apps_v1, "list_namespaced_stateful_set", namespace),
                "DaemonSets": (self.apps_v1, "list_namespaced_daemon_set", namespace),
                "Jobs": (self.batch_v1, "list_namespaced_job", namespace) if self.batch_v1 else None,
                "CronJobs": (self.batch_v1, "list_namespaced_cron_job", namespace) if self.batch_v1 else None,
                "Ingresses": (self.networking_v1, "list_namespaced_ingress", namespace) if self.networking_v1 else None,
                "Roles": (self.rbac_authorization_v1, "list_namespaced_role", namespace) if self.rbac_authorization_v1 else None,
                "RoleBindings": (self.rbac_authorization_v1, "list_namespaced_role_binding", namespace) if self.rbac_authorization_v1 else None,
            }
            
            # Remove None entries (for APIs that might not be available)
            type_mapping = {k: v for k, v in type_mapping.items() if v is not None}
            
            # Cluster-scoped resources (not namespaced)
            cluster_scoped_mapping: Dict[str, Any] = {
                "PersistentVolumes": (self.core_v1, "list_persistent_volume") if self.core_v1 else None,
                "ClusterRoles": (self.rbac_authorization_v1, "list_cluster_role") if self.rbac_authorization_v1 else None,
                "ClusterRoleBindings": (self.rbac_authorization_v1, "list_cluster_role_binding") if self.rbac_authorization_v1 else None,
            }
            cluster_scoped_mapping = {k: v for k, v in cluster_scoped_mapping.items() if v is not None}

            if object_type not in type_mapping:
                # Check if it's a CRD (Custom Resource Definition)
                if self.custom_objects and self.apiextensions_v1:
                    try:
                        # Find the CRD definition
                        crds = self.apiextensions_v1.list_custom_resource_definition()
                        for crd in crds.items:
                            if crd.spec and crd.spec.names and crd.spec.names.kind == object_type:
                                # Found the CRD, get its group, version, and plural
                                group = crd.spec.group
                                versions = crd.spec.versions if hasattr(crd.spec, 'versions') else []
                                if not versions and hasattr(crd.spec, 'version'):
                                    # Legacy CRD format
                                    version = crd.spec.version
                                    plural = crd.spec.names.plural
                                    # List custom resources
                                    try:
                                        result = self.custom_objects.list_namespaced_custom_object(
                                            group, version, namespace, plural
                                        )
                                        if isinstance(result, dict) and "items" in result:
                                            object_names = [item.get("metadata", {}).get("name", "") for item in result["items"]]
                                            return sorted([name for name in object_names if name])
                                    except Exception:
                                        return []
                                elif versions:
                                    # New CRD format with multiple versions
                                    # Use the first version that is served
                                    for v in versions:
                                        if v.served:
                                            version = v.name
                                            plural = crd.spec.names.plural
                                            try:
                                                result = self.custom_objects.list_namespaced_custom_object(
                                                    group, version, namespace, plural
                                                )
                                                if isinstance(result, dict) and "items" in result:
                                                    object_names = [item.get("metadata", {}).get("name", "") for item in result["items"]]
                                                    return sorted([name for name in object_names if name])
                                            except Exception:
                                                pass
                                    return []
                                break
                    except Exception:
                        pass
                # For types not in mapping and not CRDs, return empty list
                return []

            api_client, method_name, ns = type_mapping[object_type]
            method = getattr(api_client, method_name)
            result = method(ns)

            # Extract names from the result
            if hasattr(result, "items"):
                object_names = [item.metadata.name for item in result.items]

            sorted_names = sorted(object_names)
            debug_logger.info(f"LOAD: Fetched {len(sorted_names)} objects of type '{object_type}' in namespace '{namespace}' from K8s API")
            return sorted_names

        except ApiException as e:
            raise K8sManagerError(
                f"Failed to fetch {object_type} in {namespace}: {e.reason} (Status: {e.status})"
            ) from e
        except Exception as e:
            raise K8sManagerError(
                f"Unexpected error fetching {object_type} in {namespace}: {e}"
            ) from e

    def get_details(self, namespace: str, object_type: str, name: str) -> str:
        """
        Get YAML details of a specific object.

        Args:
            namespace: Namespace name.
            object_type: Type of object (e.g., "Pods", "Services").
            name: Name of the object.

        Returns:
            YAML representation of the object.

        Raises:
            K8sManagerError: If unable to fetch object details.
        """
        debug_logger.info(f"LOAD: Fetching details for '{object_type}/{name}' in namespace '{namespace}' from K8s API")
        if not self.core_v1:
            raise K8sManagerError("Kubernetes client not initialized")

        try:
            obj: Any = None

            # Map object types to their API methods
            type_mapping: Dict[str, Any] = {
                "Pods": (self.core_v1, "read_namespaced_pod", namespace, name),
                "Services": (self.core_v1, "read_namespaced_service", namespace, name),
                "ConfigMaps": (
                    self.core_v1,
                    "read_namespaced_config_map",
                    namespace,
                    name,
                ),
                "Secrets": (self.core_v1, "read_namespaced_secret", namespace, name),
                "ServiceAccounts": (
                    self.core_v1,
                    "read_namespaced_service_account",
                    namespace,
                    name,
                ),
                "PersistentVolumeClaims": (
                    self.core_v1,
                    "read_namespaced_persistent_volume_claim",
                    namespace,
                    name,
                ),
                "Deployments": (
                    self.apps_v1,
                    "read_namespaced_deployment",
                    namespace,
                    name,
                ),
                "ReplicaSets": (
                    self.apps_v1,
                    "read_namespaced_replica_set",
                    namespace,
                    name,
                ),
                "StatefulSets": (
                    self.apps_v1,
                    "read_namespaced_stateful_set",
                    namespace,
                    name,
                ),
                "DaemonSets": (
                    self.apps_v1,
                    "read_namespaced_daemon_set",
                    namespace,
                    name,
                ),
                "Jobs": (self.batch_v1, "read_namespaced_job", namespace, name) if self.batch_v1 else None,
                "CronJobs": (self.batch_v1, "read_namespaced_cron_job", namespace, name) if self.batch_v1 else None,
                "Ingresses": (self.networking_v1, "read_namespaced_ingress", namespace, name) if self.networking_v1 else None,
                "Roles": (self.rbac_authorization_v1, "read_namespaced_role", namespace, name) if self.rbac_authorization_v1 else None,
                "RoleBindings": (self.rbac_authorization_v1, "read_namespaced_role_binding", namespace, name) if self.rbac_authorization_v1 else None,
            }
            
            # Remove None entries
            type_mapping = {k: v for k, v in type_mapping.items() if v is not None}
            
            # Cluster-scoped resources (not namespaced)
            cluster_scoped_mapping: Dict[str, Any] = {
                "PersistentVolumes": (self.core_v1, "read_persistent_volume", name) if self.core_v1 else None,
                "ClusterRoles": (self.rbac_authorization_v1, "read_cluster_role", name) if self.rbac_authorization_v1 else None,
                "ClusterRoleBindings": (self.rbac_authorization_v1, "read_cluster_role_binding", name) if self.rbac_authorization_v1 else None,
            }
            cluster_scoped_mapping = {k: v for k, v in cluster_scoped_mapping.items() if v is not None}

            if object_type not in type_mapping:
                # Check if it's a CRD (Custom Resource Definition)
                if self.custom_objects and self.apiextensions_v1:
                    try:
                        # Find the CRD definition
                        crds = self.apiextensions_v1.list_custom_resource_definition()
                        for crd in crds.items:
                            if crd.spec and crd.spec.names and crd.spec.names.kind == object_type:
                                # Found the CRD, get its group, version, and plural
                                group = crd.spec.group
                                versions = crd.spec.versions if hasattr(crd.spec, 'versions') else []
                                if not versions and hasattr(crd.spec, 'version'):
                                    # Legacy CRD format
                                    version = crd.spec.version
                                    plural = crd.spec.names.plural
                                    # Get custom resource
                                    try:
                                        obj = self.custom_objects.get_namespaced_custom_object(
                                            group, version, namespace, plural, name
                                        )
                                        # Convert dict to YAML
                                        return yaml.dump(obj, default_flow_style=False, sort_keys=False)
                                    except Exception as e:
                                        raise K8sManagerError(f"Failed to fetch CRD {object_type}: {e}") from e
                                elif versions:
                                    # New CRD format with multiple versions
                                    # Use the first version that is served
                                    for v in versions:
                                        if v.served:
                                            version = v.name
                                            plural = crd.spec.names.plural
                                            try:
                                                obj = self.custom_objects.get_namespaced_custom_object(
                                                    group, version, namespace, plural, name
                                                )
                                                # Convert dict to YAML
                                                return yaml.dump(obj, default_flow_style=False, sort_keys=False)
                                            except Exception as e:
                                                if v == versions[-1]:  # Last version
                                                    raise K8sManagerError(f"Failed to fetch CRD {object_type}: {e}") from e
                                                continue
                                    raise K8sManagerError(f"Failed to fetch CRD {object_type}: No served version found")
                                break
                    except Exception as e:
                        raise K8sManagerError(f"Unsupported object type: {object_type}") from e
                raise K8sManagerError(f"Unsupported object type: {object_type}")

            api_client, method_name, ns, obj_name = type_mapping[object_type]
            method = getattr(api_client, method_name)
            obj = method(obj_name, ns)

            # Convert to YAML
            # Use the Kubernetes client's serialization
            from kubernetes.client import ApiClient

            api_client_instance = ApiClient()
            yaml_data = api_client_instance.sanitize_for_serialization(obj)
            yaml_output = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
            debug_logger.info(f"LOAD: Fetched details for '{object_type}/{name}' in namespace '{namespace}' (YAML size: {len(yaml_output)} chars)")
            return yaml_output

        except ApiException as e:
            raise K8sManagerError(
                f"Failed to fetch {object_type}/{name} in {namespace}: {e.reason} (Status: {e.status})"
            ) from e
        except Exception as e:
            raise K8sManagerError(
                f"Unexpected error fetching {object_type}/{name} in {namespace}: {e}"
            ) from e

    def get_logs(
        self, namespace: str, pod_name: str, container: Optional[str] = None, tail_lines: int = 100
    ) -> str:
        """
        Get logs from a pod.

        Args:
            namespace: Namespace name.
            pod_name: Name of the pod.
            container: Optional container name (if pod has multiple containers).
            tail_lines: Number of lines to retrieve (default: 100).

        Returns:
            Log output as a string.

        Raises:
            K8sManagerError: If unable to fetch logs.
        """
        debug_logger.info(f"LOAD: Fetching logs for pod '{pod_name}' in namespace '{namespace}' (container={container}, tail_lines={tail_lines}) from K8s API")
        if not self.core_v1:
            raise K8sManagerError("Kubernetes client not initialized")

        try:
            if container:
                logs = self.core_v1.read_namespaced_pod_log(
                    pod_name, namespace, container=container, tail_lines=tail_lines
                )
            else:
                logs = self.core_v1.read_namespaced_pod_log(
                    pod_name, namespace, tail_lines=tail_lines
                )
            debug_logger.info(f"LOAD: Fetched logs for pod '{pod_name}' in namespace '{namespace}' (size: {len(logs)} chars)")
            return logs
        except ApiException as e:
            raise K8sManagerError(
                f"Failed to fetch logs for pod {pod_name} in {namespace}: {e.reason} (Status: {e.status})"
            ) from e
        except Exception as e:
            raise K8sManagerError(
                f"Unexpected error fetching logs for pod {pod_name} in {namespace}: {e}"
            ) from e

