"""Module with cluster resources management"""
import json
import logging
import importlib
from pathlib import Path

import openstack
import openshift as oc
from openshift.model import OpenShiftPythonException
from novaclient import client
from dynaconf import Dynaconf
from weakget import weakget

import pipeline.utils as utils
# import product plugin entry point
module = importlib.import_module("pipeline.tasks.product_plugins." + utils.PRODUCT_PLUGIN_NAME)
manage_product_on_cluster = getattr(module, "manage_product_on_cluster")


def _get_cluster_channel(cluster_context):
    """Get cluster version from cluster resources"""
    try:
        cluster_version = oc.selector("clusterversion", static_context=cluster_context).object().as_dict()
        return weakget(cluster_version)["spec"]["channel"] % None
    except oc.OpenShiftPythonException:
        return None


def _get_cloud_provider(metadata_path):
    """Get cloud provider from cluster metadata.json file"""
    if not metadata_path.exists():
        return None

    with open(metadata_path) as f:
        metadata = json.load(f)
    return next((provider for provider in ["ovirt", "openstack", "aws"] if provider in metadata), None)


def load_clusters():
    """Load existing clusters from cluster-management module"""
    clusters = {}
    for dir_ in utils.CLUSTER_MANAGEMENT_DIR.iterdir():
        kubeconfig = dir_ / "auth" / "kubeconfig"
        if Path.exists(kubeconfig):
            kube_password_path = dir_ / "auth" / "kubeadmin-password"
            kube_password = None
            if Path.exists(kube_password_path):
                with open(kube_password_path, "r") as f:
                    kube_password = f.read()

            context = oc.api_server(kubeconfig_path=kubeconfig)
            with context:
                try:
                    api_url = oc.whoami("--show-server")
                except OpenShiftPythonException:
                    api_url = None
            channel = _get_cluster_channel(context)
            cloud = _get_cloud_provider(dir_ / "metadata.json")

            clusters[dir_.name] = {
                "dir": dir_,
                "context": context,
                "kube_password": kube_password,
                "api_url": api_url,
                "channel": channel,
                "cloud": cloud
            }

    return clusters


def check_openstack_clusters(config):
    """Verify openstack cloud resources sufficiency"""
    conn = openstack.connect(cloud="psi")
    credentials = conn.auth
    cl = client.Client("2",
                       username=credentials["username"],
                       password=credentials["password"],
                       project_id=credentials["project_id"],
                       auth_url=credentials["auth_url"],
                       user_domain_name=credentials["user_domain_name"])

    os_cfg = Dynaconf(settings_file=utils.CLUSTER_MANAGEMENT_DIR / "settings.yaml")["default"]["cloud"]["openstack"]
    os_env = next((env for env in os_cfg.environments if env.name == os_cfg.base_env), {})

    base_flavor = config["params"].get("osp-base-flavor") or os_env.get("osp_base_flavor")
    if base_flavor is None:
        raise RuntimeError(f"{utils.CLUSTER_MODULE_NAME} openstack base flavor is not configured. \n"
                           "You can set ether osp-base-flavor param or osp_base_flavor settings value")

    master_flavor = config["params"].get("master-flavor") or os_env.get("master_flavor") or base_flavor
    worker_flavor = config["params"].get("worker-flavor") or os_env.get("worker_flavor") or base_flavor

    master_replicas = config["params"].get("master-replicas") or os_env.get("master_replicas") or 3
    worker_replicas = config["params"].get("worker-replicas") or os_env.get("worker_replicas") or 3
    # find required ram for chosen flavors
    flavors = conn.list_flavors()
    master_ram = next((fl.ram for fl in flavors if fl.name == master_flavor), None)
    if master_ram is None:
        raise RuntimeError(f"Unknown master flavor: {master_flavor}")
    worker_ram = next((fl.ram for fl in flavors if fl.name == worker_flavor), None)
    if worker_ram is None:
        raise RuntimeError(f"Unknown worker flavor: {worker_flavor}")
    # count required ram and check if it's not exceed the set limit
    required_ram = master_ram * master_replicas + worker_ram * worker_replicas
    quotas = cl.quotas.get(credentials["project_id"], detail=True)
    ram_usage_after = (quotas.ram["in_use"] + required_ram) / quotas.ram["limit"]
    if ram_usage_after > (utils.MAX_OS_LOAD_PERCENTAGE / 100):
        # return
        raise RuntimeError(f"Required openstack resources exceed the set limit"
                           f"({ram_usage_after * 100}%/{utils.MAX_OS_LOAD_PERCENTAGE}%)")


def check_aws_clusters(clusters):
    """Verify aws cloud resources sufficiency"""
    # count existing aws clusters
    aws_clusters = sum(cluster["cloud"] == "aws" for cluster in clusters.values())
    if aws_clusters >= utils.MAX_AWS_CLUSTERS:
        raise RuntimeError(f"Required resources exceed set aws cluster limit"
                           f"({aws_clusters + 1}/{utils.MAX_AWS_CLUSTERS})")


def check_clusters_cloud(config, clusters):
    """Verify clusters cloud resources sufficiency"""
    if (weakget(config)["params"]["cloud"] % None) is None:
        raise RuntimeError(f"{utils.CLUSTER_MODULE_NAME} cloud provider is not set")
    cloud = config["params"]["cloud"]

    if cloud == "openstack":
        logging.info("Verify openstack resources sufficiency")
        check_openstack_clusters(config)
        logging.info("Openstack resources sufficiency verified")
    if cloud == "aws":
        logging.info("Verify aws resources sufficiency")
        check_aws_clusters(clusters)
        logging.info("Aws resources sufficiency verified")


def manage_cluster(config, ti):
    """Main cluster resource management task, inspecting all clusters and verifying their resource sufficiency"""
    if utils.ALWAYS_INSTALL_CLUSTER or not utils.FREE_DEPLOYER_WORKPLACE_CONFIG:
        return utils.CLUSTER_MANAGEMENT_SETUP_TASK_ID

    required_version = weakget(config)["params"]["installer-version"] % None
    if required_version is None:
        raise RuntimeError("openshift installer version is not specified")
    cloud = weakget(config)["params"]["cloud"] % None
    if cloud is None:
        raise RuntimeError("openshift cloud provider is not specified")

    clusters = load_clusters()
    for name, cfg in clusters.items():
        if cfg["cloud"] == cloud and cfg["channel"] == required_version:
            logging.info(f"Examining cluster: {name}")
            context = manage_product_on_cluster(cfg)
            if context:
                logging.info(f"Suitable cluster found: {name}")
                ti.xcom_push("cluster_context", context)
                return utils.CLUSTER_MANAGEMENT_END_TASK_ID
            logging.info(f"Cluster is not suitable: {name}")

    # check on resource sufficiency for the new cluster installation
    logging.info("There is no existing suitable cluster or project to run the tests on.\n"
                 "Verifying cloud provider resources sufficiency")
    check_clusters_cloud(config, clusters)
    logging.info("Resources sufficiency verified. Installing new cluster...")
    return utils.CLUSTER_MANAGEMENT_SETUP_TASK_ID
