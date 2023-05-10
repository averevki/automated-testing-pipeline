"""Example plugin module"""
from typing import Optional


def manage_product_on_cluster(cluster) -> Optional[dict]:
    """
    Entry point for the product plugin.
    Plugin should check if given cluster is available/have available namespace for testing.

    Return value must be from one of these 3 cases:
    1. Cluster is suitable and have an appropriate namespace for tests to run:
    return {"api_url": cluster["api_url"], "kube_password": cluster["kube_password"], "namespace": "found_namespace"}
    2. Cluster is suitable but doesn't have appropriate namespace for tests (new project will be created):
    return {"api_url": cluster["api_url"], "kube_password": cluster["kube_password"], "namespace": None}
    3. Cluster is not suitable for the testing on products (if there is no other suitable cluster,
    then cluster will be installed and new project will be created):
    return None

    :param cluster: checked cluster properties
    :return: Context dictionary or None
    """
    cluster_context = {"api_url": cluster["api_url"], "kube_password": cluster["kube_password"], "namespace": None}
    return None
