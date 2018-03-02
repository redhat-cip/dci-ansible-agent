# DCI Ansible Agent

## First steps

### Install the rpm

You be able to install the rpm of DCI Ansible Agent, you will need to activate some extra repositories.

If you are running RHEL7, you need to enable a couple of extra channels:

    # subscription-manager repos '--disable=*' --enable=rhel-7-server-rpms --enable=rhel-7-server-optional-rpms --enable=rhel-7-server-extras-rpms

You will also need the EPEL and DCI repositories:

    # yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
    # yum install -y https://packages.distributed-ci.io/dci-release.el7.noarch.rpm

You can now install the `dci-ansible-agent` package:

    # yum install -y dci-ansible-agent

### Configure your time source

It's important to have an chronized clock. Chrony should be started and running.
You can valide the server clock is synchronized with the following command:

    $ chronyc activity
    200 OK
    6 sources online
    0 sources offline
    0 sources doing burst (return to online)
    0 sources doing burst (return to offline)
    0 sources with unknown address

If Chrony is not running, you can follow [the official documentation](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/system_administrators_guide/sect-using_chrony) to set it up.

### Configuration

You start using the DCI Ansible Agent, you need to adjust a couple of configuration files. The first one is \`/etc/dci-ansible-agent/dcirc.sh\`:

    #!/bin/bash
    DCI_CS_URL="https://api.distributed-ci.io/"
    DCI_CLIENT_ID=<remoteci_id>
    DCI_API_SECRET=<api_secret>
    # The file is used by systemd. This is the reason why we cannot
    # use the common 'export FOO=bar' syntax.
    export DCI_CS_URL
    export DCI_CLIENT_ID
    export DCI_API_SECRET

-   DCI\_CLIENT\_ID: replace remoteci\_id with the remoteci UUID.
-   DCI\_API\_SECRET: replace api\_secret with the CI token.

If you need to go through a HTTP proxy, you will need to set the http\_proxy environment variables:

    http_proxy="http://somewhere:3128"
    https_proxy="http://somewhere:3128"
    export http_proxy
    export https_proxy

At this point, you can validate your dcirc.sh with the following commands:

    # source /etc/dci-ansible-agent/dcirc.sh
    # dcictl remoteci-list

You should get an output similar to this one:

    +--------------------------------------+-----------+--------+---------+-------+--------------+
    |                  id                  |    name   | state  | country | email | notification |
    +--------------------------------------+-----------+--------+---------+-------+--------------+
    | a2780b4c-0cdc-4a4a-a9ed-44930562ecce | RACKSPACE | active |   None  |  None |     None     |
    +--------------------------------------|-----------|--------|---------|-------|--------------+


If you get a error with the call above, you can validate the API server is
reachable with the following `curl` call:

    $ curl https://api.distributed-ci.io/api/v1
    {"_status": "OK", "message": "Distributed CI."}

------------------------------------------------------------------------

Then, you need to edit the `/etc/dci-ansible-agent/settings.yml` to adjust some settings to match you environment. The latest version of the default settings is [available on GitHub](https://github.com/redhat-cip/dci-ansible-agent/blob/master/settings.yml)

------------------------------------------------------------------------

You need adjust the following Ansible playbook to describe how you want to provision your OpenStack. These playbook are located in the /etc/dci-ansible-agent/hooks.

-   \`pre-run.yml\`: it will be call during the provisioning. This is the place where you describe the steps to follow to prepare your platform:

    > -   deployment of the undercloud machine
    > -   configuration of a network device
    > -   etc

-   \`running.yml\`: this playbook will be trigger to deploy the undercloud and the overcloud. It should also add <http://$jumpbox_ip/dci_repo/dci_repo.repo> to the repository list (/etc/yum/yum.repo.d/dci\_repo.repo).

    > At the end of the this hook run, an undercloud host should be available in Ansible inventory. It will be used later to run the test. The operation is done automatically for you if the undercloud\_ip variable has been set in the configuration. If this is not the case, you have to call add\_host by yourself at the end of the hook execution.

-   \`teardown.yml\`: this playbook clean the full playform.

### How to use the images (OSP12)

If you are use OSP12, you need to adjust your automation to fetch the images on the undercloud and make use of them during the deployment.

You will have to adjust two extra keys in your `/etc/dci-ansible-agent/dcirc.sh` file:

- DCI_REGISTRY_USER
- DCI_REGISTRY_PASSWORD

Before you start the overcloud deploy with the `openstack overcloud deploy --templates [additional parameters]` command, you have to call the following command on the undercloud node.

    $ openstack overcloud container image prepare --namespace ${jump_box}:5000/rhosp12  --output-env-file ~/docker_registry.yaml

:information_source: `${jump_box}` is the IP address of the Jumpbox machine.

You don't have to do any additional `openstack overcloud container` call unless you want to rebuild or patch an image.

The Overcloud deployment is standard, you just have to include the two following extra Heat template:

- /usr/share/openstack-tripleo-heat-templates/environments/docker.yaml
- ~/docker_registry.yaml

See the upstream documentation if you need more details: [Deploying the containerized Overcloud](https://docs.openstack.org/tripleo-docs/latest/install/containers_deployment/overcloud.html#deploying-the-containerized-overcloud)

### How to run the Upgrade

After the deployment of the OpenStack, the agent will look for an upgrade playbook.
If the playbook exists it will run it in order to upgrade the installation.

The agent expects the upgrade playbook to have the following naming convention:

     /etc/dci-ansible-agent/hooks/upgrade_from_OSP9_to_OSP10.yml

Here, `OSP9` is the current version and `OSP10` is the version to upgrade to.

### Start the service

The agent comes with a systemd configuration that simplify its execution. You can just start the agent:

    # systemctl start dci-ansible-agent

Use journalctl to follow the agent execution:

    # journalctl -ef -u dci-ansible-agent

If you need to connect as the dci-ansible-agent user, you can do:

    # su - dci-ansible-agent -s /bin/bash

This is for example necessary if you want to create a ssh key:

    $ ssh-keygen

### Use the timers

Two systemd timers are provided by the package, dci-ansible-agent.timer will ensure the agent will be call automatically severial time a day. dci-update.timer will refresh the dci packages automatically. To enable them, just run:

    # systemctl enable dci-ansible-agent.timer
    # systemctl start dci-ansible-agent.timer
    # systemctl enable dci-update.timer
    # systemctl start dci-update.timer

If you are using a HTTP proxy, you should also edit /etc/yum.conf and configure the proxy parameter to be sure the dci-update timer will be able to refresh DCI packages.

#### How to adjust the timer configuration

    # systemctl edit --full dci-ansible-agent.timer

You have to edit the value of the `OnUnitActiveSec` key. According to systemd documentation:

> OnUnitActiveSec= defines a timer relative to when the unit the timer is activating was last activated.
> OnUnitInactiveSec= defines a timer relative to when the unit the timer is activating was last deactivated.

DCI comes with a default value of 1h, you can increase to 12h for example.

### Debug: How to manually run the agent

You may want to trace the agent execution to understand a problem. In this case, you can call it manually:

    # su - dci-ansible-agent -s /bin/bash
    $ cd /usr/share/dci-ansible-agent
    $ source /etc/dci-ansible-agent/dcirc.sh
    $ /usr/bin/ansible-playbook -vv /usr/share/dci-ansible-agent/dci-ansible-agent.yml -e @/etc/dci-ansible-agent/settings.yml
