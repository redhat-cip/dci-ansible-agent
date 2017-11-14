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


def parse_image(image, private_registry):
    image_with_project, tag = image['imagename'].split(':')
    project, image_name = image_with_project.split('/')
    repo = image['pull_source']
    return {
        'repo': repo,
        'project': project,
        'image_name': image_name,
        'tag': tag,
        'src': '%s/%s/%s' % (repo, project, image_name),
        'local_name': '%s/%s:latest' % (project, image_name),
        'dest': '%s/%s/%s' % (private_registry, project, image_name),
        'dest_no_suffix': '%s/%s/%s' % (private_registry, project, image_name.replace('-docker', '')),
    }


def pull_image(image):
    print('docker pull %s:%s' % (image['src'], image['tag']))
    client.pull(image['src'], tag=image['tag'])


def tag_image(image):
    docker_image_id = client.inspect_image('%s:%s' % (image['src'], image['tag']))['Id']
    print('docker %s %s:%s' % (docker_image_id, image['dest'], 'latest'))
    client.tag(docker_image_id, repository=image['dest'], tag='latest')
    print('docker %s %s:%s' % (docker_image_id, image['dest'], 'pcmklatest'))
    client.tag(docker_image_id, repository=image['dest'], tag='pcmklatest')
    print('docker %s %s:%s' % (docker_image_id, image['dest_no_suffix'], 'latest'))
    client.tag(docker_image_id, repository=image['dest_no_suffix'], tag='latest')
    # pcmklatest are needed for some cases
    print('docker %s %s:%s' % (docker_image_id, image['dest_no_suffix'], 'pcmklatest'))
    client.tag(docker_image_id, repository=image['dest_no_suffix'], tag='pcmklatest')


def push_image(image):
    print('docker push %s:%s' % (image['dest'], 'latest'))
    client.push(image['dest'], tag='latest')
    print('docker push %s:%s' % (image['dest'], 'pcmklatest'))
    client.push(image['dest'], tag='pcmklatest')
    print('docker push %s:%s' % (image['dest_no_suffix'], 'latest'))
    client.push(image['dest_no_suffix'], tag='latest')
    print('docker push %s:%s' % (image['dest_no_suffix'], 'pcmklatest'))
    client.push(image['dest_no_suffix'], tag='pcmklatest')


def main():
    if len(sys.argv) <= 1:
        print('\nError: container_images.yaml path required\nusage: %s ./container_images.yaml' % sys.argv[0])
        sys.exit(1)

    login(DCI_REGISTRY_USER, DCI_REGISTRY_PASSWORD, DCI_REGISTRY)

    docker_distribution_config = yaml.load(open('/etc/docker-distribution/registry/config.yml', 'r'))
    private_registry = docker_distribution_config['http']['addr']

    final_container_images_yaml = {'container_images': []}
    with open(sys.argv[1], 'r') as stream:
        try:
            images = yaml.load(stream)['container_images']
            for image in images:
                print('-----------------')
                image = parse_image(image, private_registry)
                pull_image(image)
                tag_image(image)
                push_image(image)
                final_container_images_yaml['container_images'].append({
                    'imagename': image['local_name'],
                    'pull_source': private_registry})
            print('-----------------')
        except yaml.YAMLError as exc:
            print(exc)
    with open(sys.argv[2], 'w') as fd:
        yaml.dump(final_container_images_yaml, fd, default_flow_style=False)


if __name__ == '__main__':
    main()
