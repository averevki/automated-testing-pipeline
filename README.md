# Automated Testing Pipeline

## Installation

Prerequisites:
* Python 3.11
* Pipenv

After the cloning this repository on your local machine it is enough to run `pipenv install` for the installation of 
all required packages and sequential `pipenv shell` to enter python virtual environment with Apache Airflow.

## Execution

The first time execution requires setting the `$AIRFLOW_HOME` environment variable to set up the predefined 
Airflow configuration with the correct path to find the main DAG. It is enough to set value 
of this variable to `$(pwd)/airflow` by executing the `export AIRFLOW_HOME=$(pwd)/airflow` 
(it is expected for your current path to be in the pipeline repository root). 
This way, the correct path to the complete Airflow configuration file will be set.

Default path to the airflow configuration is `~/airflow`. And by skipping previous step on first execution, 
the new `airflow.cfg` config will be created in the defined path. In this config, it is enough to change the value 
of the first variable `dags_folder` to the `$PIPELINE_ROOT/pipeline/dags` or completely replace this config 
with the predefined one in the `airflow` directory. This way, config can be used for the further development.

After setting up the configuration, 
it is enough to execute the `airflow standalone` command, which will start all the necessary Airflow services. 
Next, the web server will be available at `localhost:8080`.

## Configuration

Workflow pipelines are configured using the `config/settings.yaml` and `config/settings.yaml.local` files. 
The latter one, if present, will completely overwrite the configuration in the first one. 
The meaning of each setting is described and can be studied in the `config/settings.yaml.tpl` file.

Parts of the pipeline are modules, that are residing in the `modules` directory.
The names of these modules are used in the settings files for the workflow configuration. 
It is recommended to add modules as git submodules using the `git submodule add` command.
