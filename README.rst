DCI Ansible Agent
=================

First steps
-----------

Install the rpm
~~~~~~~~~~~~~~~

You be able to install the rpm of DCI Ansible Agent, you will need to
activate some extra repositories.

If you are running RHEL7, you need to enable a couple of extra channels:

    # subscription-manager repos '--disable=*' --enable=rhel-7-server-rpms --enable=rhel-7-server-optional-rpms --enable=rhel-7-server-extras-rpms

You will also need the EPEL and DCI repositories:

    # yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
    # yum install -y https://packages.distributed-ci.io/dci-release.el7.noarch.rpm

You can know install the ``dci-ansible-agent`` package:

    # yum install -y dci-ansible-agent

Configuration
~~~~~~~~~~~~~

You start using the DCI Ansible Agent, you need to adjust a couple of
configuration files. The first one is `/etc/dci-ansible-agent/dcirc.sh`::

    #!/bin/bash
    
    DCI_CS_URL="https://api.distributed-ci.io/"
    DCI_LOGIN="my_login"
    DCI_PASSWORD="my_password"
    export DCI_CS_URL
    export DCI_LOGIN
    export DCI_PASSWORD

* DCI_LOGIN: replace `my_login` with your DCI login.
* DCI_PASSWORD: replace `my_password` with your DCI password.

------------

Then, you need to edit the `/etc/dci-ansible-agent/settings.yml` file::

    dci_topic: "OSP10"
    dci_login: "{{ lookup('env', 'DCI_LOGIN') }}"
    dci_password: "{{ lookup('env', 'DCI_PASSWORD') }}"
    dci_baseurl: "http://{{ ansible_default_ipv4.address }}"
    dci_remoteci: "test-ovb-0"
    undercloud_ip: "fooo"
    dci_mirror_location: "/var/www/html"
    dci_config_dir: "/etc/dci-ansible-agent"
    dci_cache_dir: "/var/lib/dci-ansible-agent"

------------

You need adjust the following Ansible playbook to describe how you
want to provision your OpenStack. These playbook are located in the
`/etc/dci-ansible-agent/hooks`.

* `pre-run.yml`: it will be call during the provisioning. This is the place
  where you describe the steps to follow to prepare your platform:

    * deployment of the undercloud machine
    * configuration of a network device
    * etc

* `running.yml`: this playbook will be trigger to deploy the undercloud and the overcloud. It should also add http://$jumpbox_ip/dci_repo/dci_repo.repo to the repository list (`/etc/yum/yum.repo.d/dci_repo.repo`).
* `teardown.yml`: this playbook clean the full playform.

Start the service
~~~~~~~~~~~~~~~~~

The agent comes with a systemd configuration that simplify its execution. You can just start the agent::

    # systemctl start dci-ansible-agent

Use `journalctl` to follow the agent execution::

    # journalctl -ef -u dci-ansible-agent

If you need to connect as the `dci-ansible-agent` user, you can do::

    # su - dci-ansible-agent -s /bin/bash

This is for example necessary if you want to create a ssh key::

    $ ssh-keygen

Use the timers
~~~~~~~~~~~~~~

Two systemd timers are provided by the package, `dci-ansible-agent.timer` will
ensure the agent will be call automatically severial time a day. `dci-update.timer`
will refresh the dci packages automatically. To enable them, just run::

    # systemctl enable dci-ansible-agent.timer
    # systemctl enable dci-update.timer
