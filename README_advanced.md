# DCI Ansible Agent Advanced

### How to deal with multiple OpenStack releases

When testing multiple OpenStack releases you probably have different steps (configuration, tasks, packages, etc...) according to the release.
As an example you could:

- have scripts per OpenStack versions and file path based on the dci_topic variable (ie OSP10, OSP11, etc..):

      - shell: |
          /automation_path/{{ dci_topic }}/undercloud_installation.sh

- have git branch per OpenStack versions based on the dci_topic variable :

      - git:
          repo: https://repo_url/path/to/automation.git
          dest: /automation_path
          version: '{{ dci_topic }}'

      - shell: /automation_path/undercloud_installation.sh

- use ansible condition and jinja template with the dci_topic variable :

      - shell: |
          /automation_path/build_container.sh
        when: dci_topic in ['OSP12', 'OSP13']

      - shell: >
          source /home/stack/stackrc &&
          openstack overcloud deploy --templates
          {% if dci_topic in ['OSP12', 'OSP13'] %}
          -e /usr/share/openstack-tripleo-heat-templates/environments/docker.yaml
          -e /usr/share/openstack-tripleo-heat-templates/environments/docker-ha.yaml
          {% endif %}
          -e /usr/share/openstack-tripleo-heat-templates/environments/disable-telemetry.yaml

### How to retrieve the OpenStack yum repository

During the 'new' hook, the jumpbox will create a yum repository with latest bits available.
This repository is located in the /var/www/html/dci_repo directory and accessible via HTTP at http://$jumpbox_ip/dci_repo/dci_repo.repo
There's several ways to retrieve the yum repository from the undercloud:

- Using the yum-config-manager command:

      - shell: |
          yum-config-manager --add-repo {{ dci_baseurl }}/dci_repo/dci_repo.repo
        become: true

- Using the http url:

      - get_url:
          url: '{{ dci_baseurl }}/dci_repo/dci_repo.repo'
          dest: /etc/yum.repos.d/dci_repo.repo
        become: true

- Using the ansible copy module:

      - copy:
          src: /var/www/html/dci_repo/dci_repo.repo
          dest: /etc/yum.repos.d/dci_repo.repo
        become: true

### How to fetch and use the images

If you are use OSP12 and above, the DCI agent will set up an image registry and fetch the last OSP images on your jumpbox.

Before you start the overcloud deploy with the `openstack overcloud deploy --templates [additional parameters]` command, you have to call the following command on the undercloud node.

    $ openstack overcloud container image prepare --namespace ${jump_box}:5000/rhosp12  --output-env-file ~/docker_registry.yaml

:information_source: `${jump_box}` is the IP address of the Jumpbox machine and in this example we assume you use OSP12.

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

### Red Hat Certification: How to skip its execution

Some users might want to skip the certification tests suite.

This can be done via the settings file:

    $ Add 'skip_certification: true' to the settings.yml file.

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
