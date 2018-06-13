# DCI Ansible Agent

The "jumpbox" is the host where the agent is running. It can be a virtual machine.

## Requirements

- General:
  - A valid RHSM account.
  - A RHSM pool with the following channels:
    - rhel-7-server-rpms (jumpox|undercloud)
    - rhel-7-server-cert-rpms (undercloud)
    - rhel-7-server-extras-rpms (jumpox|undercloud)
    - rhel-7-server-optional-rpms (jumpbox)
    - rhel-7-server-rh-common-rpms (undercloud)
    - rhel-ha-for-rhel-7-server-rpms (undercloud)
  - Automation scripts for undercloud/overcloud deployment. The user must be able to automatically:
    - redeploy the undercloud machine from scratch
    - install the undercloud
    - deploy the overcloud on the node of the lab

- Jumpbox:
  - Run the latest RHEL 7 release.
  - Should be able to reach:
    - https://api.distributed-ci.io (443).
    - https://packages.distributed-ci.io (443).
    - https://registry.distributed-ci.io (443).
    - RedHat CDN.
    - EPEL repository.
    - The undercloud via ssh (22) for ansible.
  - Have a static IPv4 address.
  - Have 160GB of the free space in /var.

- Undercloud/Overcloud:
  - Should be able to reach:
    - The jumpbox via http (80) for yum repositories.
    - The jumpbox via http (5000) for docker registry.

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

    > At the end of the this hook run, the Overcloud should be running.
    > If your undercloud has a dynamic IP, you must use a set_fact action to set the undercloud_ip variable. The agent needs to know its IP to run the tests.

-   \`teardown.yml\`: this playbook clean the full playform.
