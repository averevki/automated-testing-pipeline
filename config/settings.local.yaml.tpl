#default:
#  constraints:
#    product_plugin: threescale    # name of plugin with entry point (See *pipeline.tasks.product_plugins*)
#    cluster_module: cluster-management    # override default cluster module name
#    product_workplace_module: free-deployer-workplace   # override default product module name
#    limits:
#      always_install_cluster: false
#      max_aws_clusters: 3   # limit on aws clusters
#      max_os_load_percentage: 90   # limit on openstack load
#      max_products_on_cluster: 10    # limit on products on one cluster
#    context:
#      always_create_namespace: false    # skip inspection of cluster namespaces
#      cluster_namespace: "product-by-pipeline"   # used as a name for the new project or as a namespace with product if cluster-management not defined
#      cluster_url: "https://api.ocp410.example.com:6443"    # only used as jenkins cluster parameter if cluster-management module not defined
#
#  tests:
#    run_tests: true
#    jenkins_context:
#      server:
#        uri: "http://jenkins_user:user123@localhost:8080"   # jenkins uri take priority before other connection parameters if stated
#        login: "jenkins_user"
#        password: "user123"
#        host: "localhost"
#        protocol: "http"
#        port: 8080
#      job:
#        name: "prod-jobs/operator/testAll"
#        cluster_param: "OpenshiftContext__apiUrl"  # name of the jenkins parameter with the cluster API URL
#        namespace_param: "TestsuiteContext__namespace"     #name of the jenkins parameter with the project name
#        params:
#          selenium_context: "--shm-size=2g -p 4444:4444 -p 7900:7900"
#    jenkins_report:
#      send_report: true
#      email_address: "your.email@gmail.com"
#      send_from_login: "pipeline.email@gmail.com"
#      send_from_password: "qwertyiuasfdgh"    # google password for third-party apps
#
#  modules:    # sequence and names of submodules that should be executed (See *modules* folder)
#    - cluster-management:   # submodule name
#        bash: "osia"    # bash command
#        inline_params:    # parameters after bash command / subcommands (e.g. osia install ...)
#          - install
#        params:   # bash command flags (e.g. osia install --cluster-name=ocp410-aws --installer-version=stable-4.10 -v)
#          cluster-name: ocp410
#          installer-version: stable-4.10
#          cloud: openstack
#          dns-provider: nsupdate
#          osp-image-unique: null
#          cloud-env: psi
#          v: null
#    - cluster-setup-tools:
#        bash: "./cluster-setup/setup-cluster.sh"
#        inline_params:
#          - setupHtpasswdLogin
#          - setClusterScaling
#          - setTrustedInternalRegistry
#          - trustInternallyCustomCA
#          - enableImagePruning
#          - setImageContentSourcePolicy
#          - enableUserWorkloadMonitoring
#        env:    # additional environment variables (can be used for Dynaconf configs)
#          OVERLAY: template
#          NAMESPACE: tools
#    - testsuite-tools:
#        python: "install_tools.main"    # python module with function which will be executed
#        args:
#          - httpbin
#          - minio
#          - jaeger
#        kwargs:
#          debug: INFO
#    - free-deployer-workplace:
#        bash: "free-deployer"
#        inline_params:
#          - process
#        params:
#          config-name: basic_aws
#          overlay-configs:
#            - secrets.yaml
#            - nightly.yaml
#          param:
#            - project.enable=false
#
#new_cluster:   # possible another pipeline configuration (*export AIRFLOW_VAR_ENV_FOR_DYNACONF=new_cluster* before pipeline execution)
#  modules:
#    - cluster-management:
#        bash: "osia"
#        inline_params:
#          - install
#        params:
#          cluster-name: ocp410
#          installer-version: stable-4.10
#          cloud: openstack
#          dns-provider: nsupdate
#          osp-image-unique: null
#          cloud-env: psi
#          v: null
#    - cluster-setup-tools:
#        bash: "./cluster-setup/setup-cluster.sh"
#        inline_params:
#          - setupHtpasswdLogin
#          - setClusterScaling
#          - trustInternallyCustomCA
#          - enableImagePruning
#          - enableUserWorkloadMonitoring
#        env:
#          OVERLAY: template
#          NAMESPACE: tools
