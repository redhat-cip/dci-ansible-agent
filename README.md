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

If you are use OSP12 and above, the DCI agent will set up an image registry and fetch the last OSP images on your jumpbox.

Before you start the overcloud deploy with the `openstack overcloud deploy --templates [additional parameters]` command, you have to call the following command on the undercloud node.

    $ openstack overcloud container image prepare --namespace ${jump_box}:5000/rhosp12  --output-env-file ~/docker_registry.yaml

:information_source: `${jump_box}` is the IP address of the Jumpbox machine.

You don't have to do any additional `openstack overcloud container` call unless you want to rebuild or patch an image.

The Overcloud deployment is standard, you just have to include the two following extra Heat template:

- /usr/share/openstack-tripleo-heat-templates/environments/docker.yaml
- ~/docker_registry.yaml

See the upstream documentation if you need more details: [Deploying the containerized Overcloud](https://docs.openstack.org/tripleo-docs/latest/install/containers_deployment/overcloud.html#deploying-the-containerized-overcloud)

### How to run the Update and Upgrade

After the deployment of the OpenStack, the agent will look for an update or an upgrade playbook.
If the playbook exists it will run it in order to upgrade the installation.

The agent expects the upgrade playbook to have the following naming convention:

     /etc/dci-ansible-agent/hooks/upgrade_from_OSP9_to_OSP10.yml

In this example, `OSP9` is the current version and `OSP10` is the version to upgrade to.
And here is an example of an update playbook:

     /etc/dci-ansible-agent/hooks/update_OSP9.yml

### How to run my own set of tests ?

`dci-ansible-agent` ships with a pre-defined set of tests that will be run. It is however possible for anyone, in addition of the pre-defined tests, to run their own set of tests.

In order to do so, a user needs to drop the tasks to run in `/etc/dci-ansible-agent/hooks/local_tests.yml`.

**NOTE**: Tasks run in this playbook will be run from the undercloud node. To have an improved user-experience in the DCI web application, the suite should ideally returns JUnit formatted results. If not in JUnit, one will be able to download the results but not see them in the web interface directly.


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

### Red Hat Certification:  Manually restart the certification test-suite

DCI runs the Red Hat Certification test-suite at the end of a deployment. It's configuration is stored in the `/etc/redhat-certification-openstack` directory.
`/etc/redhat-certification-openstack/tempest.conf` is the configuration file of tempest. You can manually re-run a certification test with the following command:

    $ ssh stack@undercloud
    # rhcert-ci run --test cinder_volumes

In this example, `cinder_volumes` is the name of the test to re-run.

rhcert stores the log of the run in a directory in `/var/log/rhcert/runs`. For instance `/var/log/rhcert/runs/1/openstack/` is the result of the first run.

    # cd /var/log/rhcert/runs
    # ls
    1  2

Here we have two directories, each of them are the results of a `rhcert` run. The first one was probably triggered by the agent automatically.

    # cd 1
    # ls
    openstack  rhcert
    # cd openstack/
    # ls
    cinder_volumes  director  sosreport  supportable
    # ls cinder_volumes/
    boot-tempest.log             clone-tempest.log             encryption-tempest.log
    migrate-tempest.log             output.log         quota-validation_report.json
    snapshot-validation_report.json  volume-validation_report.json boot-validation_report.json
    clone-validation_report.json  encryption-validation_report.json  migrate-validation_report.json
    quota-tempest.log  snapshot-tempest.log          volume-tempest.log

Here we have the results of different sub-test run by `rhcert`. The most important file is output.log, it will give you a global overview of what have been run and the status of the different test.

### Tempest: Run a given test manually

It may be useful to restart a failing test to troubleshoot the problem:

    $ /home/stack/tempest
    $ ostestr --no-discover tempest.api.volume.admin.test_volume_retype_with_migration.VolumeRetypeWithMigrationTest

The Certification test-suite uses it's own configuration located at `/etc/redhat-certification-openstack/tempest.conf`. Is a copy of `/home/stack/tempest/etc/tempest.conf`.

### How to test several versions of OpenStack

You can off course run different versions of OpenStack with the same jumpbox. To do so, you need first to adjust the way systemd call the agent:

    # systemctl edit --full dci-ansible-agent

```ini
[Unit]
Description=DCI Ansible Agent

[Service]
Type=oneshot
WorkingDirectory=/usr/share/dci-ansible-agent
EnvironmentFile=/etc/dci-ansible-agent/dcirc.sh
ExecStart=-/usr/bin/ansible-playbook -vv /usr/share/dci-ansible-agent/dci-ansible-agent.yml -e @/etc/dci-ansible-agent/settings.yml -e dci_topic=OSP10
ExecStart=-/usr/bin/ansible-playbook -vv /usr/share/dci-ansible-agent/dci-ansible-agent.yml -e @/etc/dci-ansible-agent/settings.yml -e dci_topic=OSP11
ExecStart=-/usr/bin/ansible-playbook -vv /usr/share/dci-ansible-agent/dci-ansible-agent.yml -e @/etc/dci-ansible-agent/settings.yml -e dci_topic=OSP12
SuccessExitStatus=0
User=dci-ansible-agent

[Install]
WantedBy=default.target
```

In this example, we do a run of OSP10, OSP11 and OSP12 everytime we start the agent.
