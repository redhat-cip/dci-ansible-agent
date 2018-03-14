#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright 2017 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import sys

import docker
import requests
import yaml

client = docker.from_env()

DCI_REGISTRY = os.getenv('DCI_REGISTRY', 'registry.distributed-ci.io')
DCI_REGISTRY_USER = os.getenv('DCI_REGISTRY_USER', 'unused')
DCI_REGISTRY_PASSWORD = os.getenv('DCI_REGISTRY_PASSWORD')

if DCI_REGISTRY_PASSWORD is None:
    print('DCI_REGISTRY_PASSWORD env variables are required')
    sys.exit(1)


def login(username, password, registry):
    print('login onto %s' % registry)
    client.login(username=username, password=password, email='', registry=registry, reauth=True)


def pull_image(image):
    print('docker pull {origin_registry}/{project}/{name}:{tag}'.format(**image))
    client.pull('{origin_registry}/{project}/{name}'.format(**image), tag=image['tag'])


def tag_image(image, tag):
    docker_image_id = client.inspect_image('{origin_registry}/{project}/{name}:{tag}'.format(**image))['Id']
    print('docker tag {} {dest_registry}/{project}/{name}:{}'.format(docker_image_id, tag, **image))
    client.tag(docker_image_id, tag=tag, repository='{dest_registry}/{project}/{name}'.format(**image))


def push_image(image, tag):
    print('docker push {dest_registry}/{project}/{name} {}'.format(tag, **image))
    client.push('{dest_registry}/{project}/{name}'.format(**image), tag=tag)


def main():
    if len(sys.argv) <= 1:
        print('\nError: images_list.yaml path required\nusage: %s ./images_list.yaml' % sys.argv[0])
        sys.exit(1)

    login(DCI_REGISTRY_USER, DCI_REGISTRY_PASSWORD, DCI_REGISTRY)

    docker_distribution_config = yaml.load(open('/etc/docker-distribution/registry/config.yml', 'r'))

    with open(sys.argv[1], 'r') as stream:
        try:
            images = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

        for image in images:
            origin, tag = image.split(':')
            origin_registry, project, name = origin.split('/')
            image = {
                'name': name,
                'project': project,
                'tag': tag,
                'origin_registry': origin_registry,
                'dest_registry': docker_distribution_config['http']['addr']
            }
            pull_image(image)
            tag_image(image, 'latest')
            tag_image(image, 'pcmklatest')
            push_image(image, 'latest')
            push_image(image, 'pcmklatest')


if __name__ == '__main__':
    main()
