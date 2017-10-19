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
    +--------------------------------------+-----------+--------+---------+-------+--------------+

------------------------------------------------------------------------

Then, you need to edit the /etc/dci-ansible-agent/settings.yml file:

    dci_topic: "OSP10"
    dci_baseurl: "http://{{ ansible_default_ipv4.address }}"
    undercloud_ip: "fooo"
    dci_mirror_location: "/var/www/html"
    dci_config_dir: "/etc/dci-ansible-agent"
    dci_cache_dir: "/var/lib/dci-ansible-agent"

undercloud\_ip is probably the sole parameter that you have to change for a first run.

------------------------------------------------------------------------

You need adjust the following Ansible playbook to describe how you want to provision your OpenStack. These playbook are located in the /etc/dci-ansible-agent/hooks.

-   \`pre-run.yml\`: it will be call during the provisioning. This is the place where you describe the steps to follow to prepare your platform:

    > -   deployment of the undercloud machine
    > -   configuration of a network device
    > -   etc

-   \`running.yml\`: this playbook will be trigger to deploy the undercloud and the overcloud. It should also add <http://$jumpbox_ip/dci_repo/dci_repo.repo> to the repository list (/etc/yum/yum.repo.d/dci\_repo.repo).

    > At the end of the this hook run, an undercloud host should be available in Ansible inventory. It will be used later to run the test. The operation is done automatically for you if the undercloud\_ip variable has been set in the configuration. If this is not the case, you have to call add\_host by yourself at the end of the hook execution.

-   \`teardown.yml\`: this playbook clean the full playform.

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
