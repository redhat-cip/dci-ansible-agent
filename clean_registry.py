#!/usr/bin/env python

import requests
import subprocess
import yaml


docker_distribution_config = yaml.load(open('/etc/docker-distribution/registry/config.yml', 'r'))
dest_registry = docker_distribution_config['http']['addr']
api_base = "http://{}/v2".format(dest_registry)

def list_repositories():
    r = requests.get(api_base + '/_catalog?n=1000')
    return r.json()['repositories']


def list_tags(repo):
    r = requests.get(api_base + '/' + repo + '/tags/list')
    return r.json().get('tags') or []


def get_refhash_from_tag(repo, tag):
    url = api_base + '/' + repo + '/manifests/' + tag
    r = requests.get(url, headers={'Accept': 'application/vnd.docker.distribution.manifest.v2+json'})
    if r.status_code == 404:
        return
    return r.headers['docker-content-digest']

refhashs_to_prune = []
for repo in list_repositories():
    for tag in list_tags(repo):
        refhash = get_refhash_from_tag(repo, tag)
        if refhash is None:
            continue
        r = requests.delete(api_base + '/' + repo + '/manifests/' + refhash)

subprocess.check_call([
    '/usr/bin/registry',
    'garbage-collect',
    '/etc/docker-distribution/registry/config.yml'])
