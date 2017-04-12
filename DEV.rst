To run the agent on a developer environment
===========================================

    $ sudo yum install -y dci-ansible
    $ ./fetch_roles
    $ ansible-playbook -vv dci-ansible-agent.yml -e dci_remoteci=test-ovb-0 -e dci_config_dir=. -e dci_cache_dir=. -e undercloud_ip=localhost -e dci_mirror_location=http://127.0.0.1 -e dci_topic=OSP10
