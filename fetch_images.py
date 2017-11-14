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

DEST_REGISTRY = os.getenv('DEST_REGISTRY', 'registry.distributed-ci.io')
DEST_REGISTRY_USER = os.getenv('DEST_REGISTRY_USER', 'unused')
DEST_REGISTRY_PASSWORD = os.getenv('DEST_REGISTRY_PASSWORD')

if DEST_REGISTRY_PASSWORD is None:
    print('DEST_REGISTRY_PASSWORD env variables are required')
    sys.exit(1)


def login(username, password, registry):
    print('login onto %s' % registry)
    client.login(username=username, password=password, email='', registry=registry, reauth=True)


def parse_image(image):
    image_with_project, tag = image['imagename'].split(':')
    project, image_name = image_with_project.split('/')
    repo = image['pull_source']
    return {
        'repo': repo,
        'project': project,
        'image_name': image_name,
        'tag': tag,
        'src': '%s/%s/%s' % (repo, project, image_name),
	'local_name': '%s:%s' % (image_name, tag),
    }


def pull_image(image):
    print('docker pull %s:%s' % (image['src'], image['tag']))
    client.pull(image['src'], tag=image['tag'])


def tag_image(image):
    docker_image_id = client.inspect_image('%s:%s' % (image['src'], image['tag']))['Id']
    client.tag(docker_image_id, repository=image['project'] + '/' + image['image_name'], tag=image['tag'])


def main():
    if len(sys.argv) <= 1:
        print('\nError: container_images.yaml path required\nusage: %s ./container_images.yaml' % sys.argv[0])
        sys.exit(1)

    login(DEST_REGISTRY_USER, DEST_REGISTRY_PASSWORD, DEST_REGISTRY)

    docker_distribution_config = yaml.load(open('/etc/docker-distribution/registry/config.yml', 'r'))
    private_registry = docker_distribution_config['http']['addr']
    print(private_registry)
    print(docker_distribution_config)

    final_container_images_yaml = {'container_images': []}
    with open(sys.argv[1], 'r') as stream:
        try:
            images = yaml.load(stream)['container_images']
            for image in images:
                print('-----------------')
                image = parse_image(image)
                print(image)
                pull_image(image)
                tag_image(image)
                final_container_images_yaml['container_images'].append({
                    'imagename': image['local_name'],
                    'pull_source': private_registry})
            print('-----------------')
        except yaml.YAMLError as exc:
            print(exc)
    print(final_container_images_yaml)
    with open(sys.argv[2], 'w') as fd:
        yaml.dump(final_container_images_yaml, fd, default_flow_style=False)

#/etc/docker-distribution/registry/config.yml

if __name__ == '__main__':
    main()
