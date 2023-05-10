"""
`Global` variables declaration and dynaconf settings parsing
Try to keep all statements here on one line please (e.g. no multiline comprehensions)
"""
from pathlib import Path

from weakget import weakget

from pipeline.config import settings

# constraints
PRODUCT_PLUGIN_NAME = weakget(settings)["constraints"]["product_plugin"] % ""
CLUSTER_MODULE_NAME = weakget(settings)["constraints"]["cluster_module"] % "cluster-management"
PRODUCT_WORKPLACE_MODULE_NAME = weakget(settings)["constraints"]["product_workplace_module"] % "free-deployer-workplace"
# constraints limits
ALWAYS_INSTALL_CLUSTER = weakget(settings)["constraints"]["limits"]["always_install_cluster"] % False
MAX_AWS_CLUSTERS = weakget(settings)["constraints"]["limits"]["max_aws_clusters"] % 3
MAX_OS_LOAD_PERCENTAGE = weakget(settings)["constraints"]["limits"]["max_os_load_percentage"] % 90
MAX_PRODUCTS_ON_CLUSTER = weakget(settings)["constraints"]["limits"]["max_products_on_cluster"] % 10
# constraints context
CLUSTER_LOGIN = weakget(settings)["constraints"]["context"]["cluster_login"] % ""
CLUSTER_PASSWORD = weakget(settings)["constraints"]["context"]["cluster_password"] % ""
ALWAYS_CREATE_NAMESPACE = weakget(settings)["constraints"]["context"]["always_create_namespace"] % False
CLUSTER_NAMESPACE = weakget(settings)["constraints"]["context"]["cluster_namespace"] % "testing-namespace"
CLUSTER_URL = weakget(settings)["constraints"]["context"]["cluster_url"] % ""
# tests
RUN_TESTS = weakget(settings)["tests"]["run_tests"] % True
# jenkins context
JENKINS_URI = weakget(settings)["tests"]["jenkins_context"]["server"]["uri"] % ""
JENKINS_LOGIN = weakget(settings)["tests"]["jenkins_context"]["server"]["login"] % ""
JENKINS_PASSWORD = weakget(settings)["tests"]["jenkins_context"]["server"]["password"] % ""
JENKINS_HOST = weakget(settings)["tests"]["jenkins_context"]["server"]["host"] % "localhost"
JENKINS_PORT = weakget(settings)["tests"]["jenkins_context"]["server"]["port"] % 8080
JENKINS_PROTOCOL = weakget(settings)["tests"]["jenkins_context"]["server"]["protocol"] % "https"
# jenkins job
JENKINS_JOB_NAME = weakget(settings)["tests"]["jenkins_context"]["job"]["name"] % ""
JENKINS_CLUSTER_PARAM = weakget(settings)["tests"]["jenkins_context"]["job"]["cluster_param"] % ""
JENKINS_NAMESPACE_PARAM = weakget(settings)["tests"]["jenkins_context"]["job"]["namespace_param"] % ""
JENKINS_JOB_PARAMS = weakget(settings)["tests"]["jenkins_context"]["job"]["params"] % {}
# jenkins report
SEND_REPORT = weakget(settings)["tests"]["jenkins_report"]["send_report"] % False
REPORT_EMAIL = weakget(settings)["tests"]["jenkins_report"]["email_address"] % ""
SEND_FROM_LOGIN = weakget(settings)["tests"]["jenkins_report"]["send_from_login"] % None
SEND_FROM_PASSWORD = weakget(settings)["tests"]["jenkins_report"]["send_from_password"] % None

# paths
ROOT = Path(__file__).parents[2]
MODULES = (ROOT / "modules").resolve()
CLUSTER_MANAGEMENT_DIR = (MODULES / CLUSTER_MODULE_NAME).resolve()
FREE_DEPLOYER_WORKPLACE_DIR = (MODULES / PRODUCT_WORKPLACE_MODULE_NAME).resolve()
# submodule configs
_CLUSTER_MANAGEMENT_MODULE = next((cfg for cfg in settings.modules if cfg.get(CLUSTER_MODULE_NAME)), {})
CLUSTER_MANAGEMENT_CONFIG = weakget(_CLUSTER_MANAGEMENT_MODULE)[CLUSTER_MODULE_NAME] % None
_FREE_DEPLOYER_WORKPLACE_MODULE = next((cfg for cfg in settings.modules if cfg.get(PRODUCT_WORKPLACE_MODULE_NAME)), {})
FREE_DEPLOYER_WORKPLACE_CONFIG = weakget(_FREE_DEPLOYER_WORKPLACE_MODULE)[PRODUCT_WORKPLACE_MODULE_NAME] % None

# names
MAIN_PIPELINE_NAME = "main-pipeline-group"
TEST_GROUP_NAME = "tests-group"

CLUSTER_MANAGEMENT_START_NAME = "manage-cluster-start"
CLUSTER_MANAGEMENT_START_TASK_ID = f"{MAIN_PIPELINE_NAME}.{CLUSTER_MODULE_NAME}-group.{CLUSTER_MANAGEMENT_START_NAME}"
CLUSTER_MANAGEMENT_END_NAME = "manage-cluster-end"
CLUSTER_MANAGEMENT_END_TASK_ID = f"{MAIN_PIPELINE_NAME}.{CLUSTER_MODULE_NAME}-group.{CLUSTER_MANAGEMENT_END_NAME}"
CLUSTER_MANAGEMENT_SETUP_NAME = f"{CLUSTER_MODULE_NAME}-setup"
CLUSTER_MANAGEMENT_SETUP_TASK_ID = f"{MAIN_PIPELINE_NAME}.{CLUSTER_MODULE_NAME}-group.{CLUSTER_MANAGEMENT_SETUP_NAME}"

PRODUCT_MANAGEMENT_START_NAME = "manage-product-start"
PRODUCT_MANAGEMENT_START_TASK_ID = f"{MAIN_PIPELINE_NAME}.{PRODUCT_WORKPLACE_MODULE_NAME}-group.{PRODUCT_MANAGEMENT_START_NAME}"
PRODUCT_MANAGEMENT_END_NAME = "manage-product-end"
PRODUCT_MANAGEMENT_END_TASK_ID = f"{MAIN_PIPELINE_NAME}.{PRODUCT_WORKPLACE_MODULE_NAME}-group.{PRODUCT_MANAGEMENT_END_NAME}"
PRODUCT_MANAGEMENT_SETUP_NAME = f"{PRODUCT_WORKPLACE_MODULE_NAME}-setup"
PRODUCT_MANAGEMENT_SETUP_TASK_ID = f"{MAIN_PIPELINE_NAME}.{PRODUCT_WORKPLACE_MODULE_NAME}-group.{PRODUCT_MANAGEMENT_SETUP_NAME}"

TESTS_START_NAME = "run-tests-start"
TESTS_START_TASK_ID = f"{MAIN_PIPELINE_NAME}.{TEST_GROUP_NAME}.{TESTS_START_NAME}"
TESTS_END_NAME = "run-tests-end"
TESTS_END_TASK_ID = f"{MAIN_PIPELINE_NAME}.{TEST_GROUP_NAME}.{TESTS_END_NAME}"
TESTS_RUN_NAME = "run-tests"
TESTS_RUN_TASK_ID = f"{MAIN_PIPELINE_NAME}.{TEST_GROUP_NAME}.{TESTS_RUN_NAME}"
