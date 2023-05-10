"""Config modules processing"""
import logging
import importlib
from typing import Optional, Callable

import openshift as oc
from airflow.decorators import task_group
from airflow.operators.bash import BashOperator
from airflow.utils.trigger_rule import TriggerRule

import pipeline.utils as utils
from pipeline.utils.utils import resolve_environment_installation_command
from pipeline.utils.builders import build_bash_task, build_python_task, build_branch_python_task, build_empty_task
from pipeline.tasks.resources_management.cluster_resources import load_clusters


def resolve_environment(module_name: str) -> Optional[BashOperator]:
    """Resolve submodule environment(pipenv/poetry) and add corresponding task for the dependencies installation"""
    task_id = f"{module_name}-setup"
    submodule_path = utils.MODULES / module_name

    env_install_command = resolve_environment_installation_command(submodule_path)
    if env_install_command is not None:
        return build_bash_task(task_id, env_install_command, str(submodule_path))


def resolve_bash_command(module_config) -> str:
    """Create string with bash command from module parameters"""
    bash_command = module_config["bash"]

    if module_config.get("inline_params") is not None:
        bash_command = " ".join([bash_command, *module_config['inline_params']])

    if module_config.get("params") is not None:
        for key, value in module_config["params"].items():
            param_string = f" {'-' if len(key) > 1 else ''}-{key}"

            if isinstance(value, list):
                param_string = " ".join([param_string, *value])
            elif value is not None:
                param_string = f"{param_string}={value}"

            bash_command += param_string

    return bash_command


def resolve_bash_task(module_name: str, module_config: dict, env_task: Optional[BashOperator] = None) -> BashOperator:
    """Create bash task from the specified parameters"""
    task_id = module_name
    cwd = utils.MODULES / module_name
    env = module_config.get("env")

    bash_command = resolve_bash_command(module_config)
    if env_task is not None:
        environment_provider = env_task.bash_command.split()[0]
        bash_command = f"{environment_provider} run " + bash_command
    # empty space at the end for Jinja templating compatibility
    bash_command += " "

    return build_bash_task(task_id, bash_command, str(cwd), env)


def resolve_python_task(module_name: str, module_config: dict):
    """Create python task from the specified parameters"""
    import_func = f"modules.{module_name}." + module_config["python"]
    import_path, function = import_func.rsplit('.', 1)
    module = importlib.import_module(import_path)
    callable_ = getattr(module, function)

    return build_python_task(task_id=module_name,
                             callable_=callable_,
                             op_args=module_config.get("args"),
                             op_kwargs=module_config.get("kwargs"))


def manage_product_task(ti):
    """Branching task, deciding if product should be installed"""
    cluster_context = ti.xcom_pull(task_ids=utils.CLUSTER_MANAGEMENT_START_TASK_ID, key="cluster_context")
    if not cluster_context or cluster_context["namespace"] is None:
        logging.info("Product installation is NOT skipped")
        return utils.PRODUCT_MANAGEMENT_SETUP_TASK_ID
    logging.info("Product installation is skipped")
    return utils.PRODUCT_MANAGEMENT_END_TASK_ID


def manage_context_task(config, ti):
    """Cluster installation endpoint, used to fetch cluster context for the future tasks"""
    cluster_context = ti.xcom_pull(task_ids=utils.CLUSTER_MANAGEMENT_START_TASK_ID, key="cluster_context")

    if cluster_context is None:
        new_cluster_name = config["params"]["cluster-name"]
        try:
            new_cluster = load_clusters()[new_cluster_name]
        except KeyError:
            raise RuntimeError("New cluster wasn't properly installed")
        cluster_url = new_cluster["api_url"]
        kube_password = new_cluster["kube_password"]
    else:
        cluster_url = cluster_context["api_url"]
        kube_password = cluster_context["kube_password"]

    logging.info(f"Setting cluster context: {cluster_url}")
    build_bash_task("cluster-login", f"oc login --username kubeadmin --password {kube_password} "
                                     f"--insecure-skip-tls-verify {cluster_url}").execute({})
    assert oc.whoami("--show-server") == cluster_url

    if cluster_context is None or cluster_context["namespace"] is None:
        namespace = utils.CLUSTER_NAMESPACE
        oc_project_command = f"oc new-project {namespace}"
    else:
        namespace = cluster_context['namespace']
        oc_project_command = f"oc project {namespace}"

    logging.info(f"Setting project context: {namespace}")
    build_bash_task("set-project-context", oc_project_command).execute({})
    assert oc.get_project_name() == namespace

    return {"api_url": cluster_url, "namespace": namespace}


def task_from_module(module: dict) -> Callable:
    """Resolve config action and return list of action tasks"""
    module_name = list(module.keys())[0]
    module_config = module[module_name]

    if not (module_config.get("bash") is None) ^ (module_config.get("python") is None):
        raise Exception(f"{module_name} must specify exactly one operator - python or bash")

    @task_group(group_id=f"{module_name}-group")
    def create_task_group():
        from pipeline.utils.utils import connect_tasks
        from pipeline.tasks.resources_management.cluster_resources import manage_cluster

        tasks = []
        # create module task
        if module_config.get("bash") is not None:
            # create environment task if needed
            environment_task = resolve_environment(module_name)
            if environment_task is not None:
                tasks.append(environment_task)

            tasks.append(resolve_bash_task(module_name, module_config, environment_task))
        elif module_config.get("python") is not None:
            tasks.append(resolve_python_task(module_name, module_config))

        if module_name == utils.CLUSTER_MODULE_NAME:
            manage_cluster_start = build_branch_python_task(
                utils.CLUSTER_MANAGEMENT_START_NAME,
                manage_cluster, [module_config]
            )
            manage_cluster_end = build_python_task(
                utils.CLUSTER_MANAGEMENT_END_NAME, manage_context_task,
                [module_config], trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
            )
            manage_cluster_start >> manage_cluster_end

            tasks.insert(0, manage_cluster_start)
            tasks.append(manage_cluster_end)
        elif module_name == utils.PRODUCT_WORKPLACE_MODULE_NAME:
            manage_product_start = build_branch_python_task(
                utils.PRODUCT_MANAGEMENT_START_NAME,
                manage_product_task
            )
            manage_product_end = build_empty_task(
                utils.PRODUCT_MANAGEMENT_END_NAME,
                TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
            )
            manage_product_start >> manage_product_end

            tasks.insert(0, manage_product_start)
            tasks.append(manage_product_end)

        connect_tasks(tasks)

    return create_task_group
