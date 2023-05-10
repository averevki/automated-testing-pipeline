"""Plugin for 3scale testing"""
import subprocess
import yaml
import base64
import logging
from typing import Optional

import openshift as oc
from openshift.model import OpenShiftPythonException
from openshift import APIObject
from weakget import weakget

import pipeline.utils as utils
from pipeline.utils.utils import resolve_environment_installation_command


def load_product_configuration() -> dict:
    """Fetch apimanager step from free-deployer config"""
    module_config = utils.FREE_DEPLOYER_WORKPLACE_CONFIG

    params = module_config["params"]
    overlays = params.get("overlay-configs")
    base_config = params.get("base-config")
    config_name = params["config-name"]

    env_command = resolve_environment_installation_command(utils.FREE_DEPLOYER_WORKPLACE_DIR)
    subprocess.run(env_command, shell=True, cwd=utils.FREE_DEPLOYER_WORKPLACE_DIR)

    flatten_command = f"{env_command.split()[0]} run free-deployer flatten "
    if overlays is not None:
        flatten_command += f"--overlay-configs {''.join(f'{cfg} ' for cfg in overlays)}"
    if base_config is not None:
        flatten_command += f"--base-config {base_config}"

    configs = subprocess.run(flatten_command, shell=True,
                             cwd=utils.FREE_DEPLOYER_WORKPLACE_DIR, capture_output=True)
    configs_yaml = yaml.safe_load(configs.stdout)
    config_steps = configs_yaml["configs"][config_name]["steps"]
    return next(step["apimanager"] for step in config_steps if "apimanager" in step)


def get_required_databases() -> dict:
    """Get settings-set databases"""
    api_manager = load_product_configuration()

    ext_system_db = weakget(api_manager)["external_dbs"]["system_db"] % False
    if ext_system_db is not False:
        if ext_system_db["url"].startswith("postgresql"):
            ext_system_db = "postgresql"
        elif ext_system_db["url"].startswith("mysql"):
            ext_system_db = "mysql"

    return {
        "system_database": api_manager.get("system_database", "mysql"),     # mysql is default db
        "external_dbs": {
            "ext_system_db": ext_system_db,
            "ext_system_redis": weakget(api_manager)["external_dbs"]["system_redis"] % False,
            "ext_backend_redis": weakget(api_manager)["external_dbs"]["backend_redis"] % False,
            "ext_zync_db": weakget(api_manager)["external_dbs"]["zync_db"] % False
        }
    }


def get_existing_databases(apiman: APIObject, cluster_context) -> dict:
    """Get existing product databases"""
    apiman_spec = apiman.as_dict()["spec"]
    # get internal system database
    system_database = weakget(apiman_spec)["system"]["database"] % None
    if system_database is not None:
        # get system database
        if system_database is not None:
            if system_database.get("mysql") is not None:
                system_database = "mysql"
            elif system_database.get("postgresql") is not None:
                system_database = "postgresql"
    # get external system database
    ext_system_db = weakget(apiman_spec)["externalComponents"]["system"]["database"] % False
    if ext_system_db is not False:
        with cluster_context:
            with oc.project(apiman.namespace()):
                db_secret = oc.selector("Secret/system-database", all_namespaces=False).object(
                    ignore_not_found=True)
        decoded_db_url = weakget(db_secret.as_dict())["data"]["URL"] % None
        if decoded_db_url:
            encoded_db_url = base64.b64decode(decoded_db_url).decode("UTF-8")

            if encoded_db_url.startswith("mysql"):
                ext_system_db = "mysql"
            elif encoded_db_url.startswith("postgresql"):
                ext_system_db = "postgresql"

    return {
        "system_database": system_database,
        "external_dbs": {
            "ext_system_db": ext_system_db,
            "ext_system_redis": weakget(apiman_spec)["externalComponents"]["system"]["redis"] % False,
            "ext_backend_redis": weakget(apiman_spec)["externalComponents"]["backend"]["redis"] % False,
            "ext_zync_db": weakget(apiman_spec)["externalComponents"]["zync"]["database"] % False
        }
    }


def compare_databases(db1: dict, db2: dict) -> bool:
    """Compare required and existing product databases"""
    # compare internal/external system database
    if db1["external_dbs"]["ext_system_db"] != db2["external_dbs"]["ext_system_db"]:
        return False
    if db1["external_dbs"]["ext_system_db"] is False:
        if db1["system_database"] != db2["system_database"]:
            return False
    # compare other external databases
    db1_ext_dbs = db1["external_dbs"]
    db2_ext_dbs = db2["external_dbs"]
    if db1_ext_dbs["ext_system_redis"] != db2_ext_dbs["ext_system_redis"]:
        return False
    if db1_ext_dbs["ext_backend_redis"] != db2_ext_dbs["ext_backend_redis"]:
        return False
    if db1_ext_dbs["ext_zync_db"] != db2_ext_dbs["ext_zync_db"]:
        return False
    return True


def manage_product_on_cluster(cluster) -> Optional[dict]:
    """
    Entry point for the product plugin.
    Plugin should check if given cluster is available/have available namespace for testing.

    Return value must be from one of these 3 cases:
    1. Cluster is suitable and has an appropriate namespace for tests to run:
    return {"api_url": cluster["api_url"], "kube_password": cluster["kube_password"], "namespace": "found_namespace"}
    2. Cluster is suitable but doesn't have an appropriate namespace for tests (new project will be created):
    return {"api_url": cluster["api_url"], "kube_password": cluster["kube_password"], "namespace": None}
    3. Cluster is not suitable for the testing on products (if there is no other suitable cluster,
    then cluster will be installed and new project will be created):
    return None

    :param cluster: checked cluster properties
    :return: Context dictionary or None
    """
    cluster_context = {"api_url": cluster["api_url"], "kube_password": cluster["kube_password"], "namespace": None}

    try:
        api_managers = oc.selector("APIManager", all_namespaces=True, static_context=cluster["context"]).objects()
    except OpenShiftPythonException:
        logging.info(f"Suitable cluster context(Cluster doesn't have required resource type): {cluster_context}")
        return cluster_context

    if not utils.ALWAYS_CREATE_NAMESPACE:
        required_databases = get_required_databases()
        # get product databases
        for apiman in api_managers:
            apiman_namespace = apiman.namespace()
            logging.info(f"Examining namespace: {apiman_namespace}")
            existing_databases = get_existing_databases(apiman, cluster["context"])
            if compare_databases(required_databases, existing_databases):
                logging.info(f"Suitable namespace found: {apiman_namespace}")
                cluster_context["namespace"] = apiman_namespace
                break
            logging.info(f"Namespace is not suitable: {apiman_namespace}")
    else:
        logging.info(f"Namespaces inspection is skipped (always_create_namespace: {utils.ALWAYS_CREATE_NAMESPACE})")
        if len(api_managers) >= utils.MAX_PRODUCTS_ON_CLUSTER:
            logging.info(f"Number of products on cluster exceeding set limit: "
                         f"{len(api_managers)}/{utils.MAX_PRODUCTS_ON_CLUSTER}")
            return None

    # return cluster context
    logging.info(f"Suitable cluster context: {cluster_context}")
    return cluster_context
