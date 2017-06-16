# ansible-role-openstack-stackdump

An Ansible role to run and retrieve [tripleo-stack-dump](https://github.com/goneri/tripleo-stack-dump) result

## Role Variables

This is the list of role variables :

  * `stackdump_result_filename`: Name of the generated file. Default to `tripleo-stack-dump.json`
  * `stackdump_stackname`: The name of the stack to dump. Default to `overcloud`.


## Dependencies

None.


## Example Playbook

The simplest way to use this module:

```
- name: Gather the stackdump from the overcloud stack
  hosts: undercloud
  roles:
    - stackdump
```

One can specify the name of the stack to dump:

```
- name: Gather the stackdump from the overcloud-preprod stack
  hosts: undercloud
  vars:
    stackdump_stackname: overcloud-preprod
  roles:
    - stackdump
```


## License

Apache 2.0


## Author Information

Distributed-CI Team  <distributed-ci@redhat.com>
